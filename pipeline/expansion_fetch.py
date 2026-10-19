"""Collect pinned path-B metadata and archives without executing package code."""
import argparse
import hashlib
import json
import re
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

from collect import recent_pairs
from registry_fetch import integrity_ok
from samples import load_jsonl
from wyss import write_jsonl

ARCHIVE_LIMIT = 32 * 1024 * 1024


def get(url, limit):
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != 'https' or parsed.hostname != 'registry.npmjs.org':
        raise ValueError('Only the npm registry is allowed')
    for attempt in range(3):
        try:
            request = urllib.request.Request(url, headers={'User-Agent': 'IntentDiff-RAG-research/1'})
            with urllib.request.urlopen(request, timeout=25) as response:
                final = urllib.parse.urlparse(response.url)
                if final.scheme != 'https' or final.hostname != 'registry.npmjs.org':
                    raise ValueError('Unexpected redirect host')
                if int(response.headers.get('Content-Length', 0)) > limit:
                    raise ValueError('Download exceeds byte limit')
                payload = response.read(limit + 1)
                if len(payload) > limit:
                    raise ValueError('Download exceeds byte limit')
                return payload
        except OSError:
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)


def write_atomic(path, payload):
    temp = path.with_suffix('.part')
    temp.write_bytes(payload)
    temp.replace(path)


def package_queue(rows, rank_limit=250):
    queue = {}
    for row in rows:
        if row['inspection_rank'] > rank_limit:
            continue
        name = row['name']
        if not re.fullmatch(r'(?:@[a-z0-9._~-]+/)?[a-z0-9._~-]+', name):
            raise ValueError('Invalid package identity')
        entry = queue.setdefault(name, {'name': name, 'searches': []})
        entry['searches'].append({k: row[k] for k in
                                 ('search_category', 'inspection_rank', 'keywords', 'metadata_files')})
    return sorted(queue.values(), key=lambda r: hashlib.sha256(r['name'].encode()).hexdigest())


def fetch_metadata(row, cache):
    key = hashlib.sha256(row['name'].encode()).hexdigest()
    path = cache / f'{key}.json'
    url = 'https://registry.npmjs.org/' + urllib.parse.quote(row['name'], safe='@')
    try:
        if not path.exists():
            write_atomic(path, get(url, 64 * 1024 * 1024))
        document = json.loads(path.read_bytes())
        if document.get('name') != row['name']:
            raise ValueError('Registry package identity mismatch')
        return dict(row, metadata_file=str(path), metadata_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                    fetched_at=datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(), url=url)
    except Exception as exc:
        return dict(row, error=f'{type(exc).__name__}: {exc}', url=url)


def pairs_at_cutoff(row, cutoff):
    document = json.loads(Path(row['metadata_file']).read_text())
    times = document.get('time', {})
    valid = {}
    missing = []
    for version, manifest in document.get('versions', {}).items():
        try:
            stamp = datetime.fromisoformat(times[version].replace('Z', '+00:00'))
        except (KeyError, ValueError, TypeError):
            missing.append(version)
            continue
        if stamp <= cutoff:
            valid[version] = manifest
    filtered = dict(document, versions=valid,
                    time={v: datetime.fromisoformat(times[v].replace('Z', '+00:00')).isoformat()
                          for v in valid})
    pairs = []
    for order, (before, after) in enumerate(recent_pairs(filtered), 1):
        if not all(re.fullmatch(r'[0-9A-Za-z.+_-]+', v) for v in (before, after)):
            raise ValueError('Unsafe version identity')
        manifests = [valid[v] for v in (before, after)]
        if any((m.get('name'), m.get('version')) != (row['name'], v)
               for m, v in zip(manifests, (before, after))):
            raise ValueError('Version manifest identity mismatch')
        publishers = [(m.get('_npmUser') or {}).get('name') for m in manifests]
        pairs.append(dict(id=f"{row['name']}@{after}", name=row['name'], before=before, after=after,
                          pair_order=order, published_before=times[before], published_after=times[after],
                          searches=row['searches'], publishers=publishers,
                          same_publisher=bool(publishers[0]) and publishers[0] == publishers[1],
                          metadata_file=row['metadata_file'], metadata_sha256=row['metadata_sha256'],
                          annotation_status='pending', gold_label=None, source='npm-path-b'))
    return pairs, missing


def fetch_archive(row, cache):
    key = hashlib.sha256(f"{row['name']}@{row['version']}".encode()).hexdigest()
    path = cache / f'{key}.tgz'
    try:
        payload = path.read_bytes() if path.exists() else get(row['dist']['tarball'], ARCHIVE_LIMIT)
        if len(payload) > ARCHIVE_LIMIT or not integrity_ok(payload, row['dist']):
            raise ValueError('Archive size or integrity check failed')
        if not path.exists():
            write_atomic(path, payload)
        return dict(row, tarball=str(path), bytes=len(payload),
                    sha256=hashlib.sha256(payload).hexdigest(), registry_integrity_verified=True)
    except Exception as exc:
        return dict(row, error=f'{type(exc).__name__}: {exc}')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', choices=['metadata', 'archives'])
    parser.add_argument('--out', required=True)
    parser.add_argument('--workers', type=int, default=6)
    args = parser.parse_args()
    out = Path(args.out)
    protocol = json.loads((out / 'protocol.json').read_text())
    cache = Path(protocol['cache'])
    (cache / 'metadata').mkdir(parents=True, exist_ok=True)
    (cache / 'tarballs').mkdir(parents=True, exist_ok=True)
    if args.stage == 'metadata':
        queue = package_queue(load_jsonl('data/acquisition/hn.path-b-packages.jsonl'))
        write_jsonl(out / 'path-b-package-queue.jsonl', queue)
        rows = []
        with ThreadPoolExecutor(max_workers=args.workers) as executor, (out / 'metadata.jsonl').open('w') as stream:
            for row in executor.map(lambda r: fetch_metadata(r, cache / 'metadata'), queue):
                rows.append(row)
                stream.write(json.dumps(row) + '\n')
                stream.flush()
                if len(rows) % 25 == 0 or len(rows) == len(queue):
                    print(json.dumps({'metadata': len(rows), 'total': len(queue),
                                      'errors': sum('error' in r for r in rows)}), flush=True)
        pairs, deferred, missing_times, failures = [], [], [], []
        cutoff = datetime.fromisoformat(protocol['cutoff'])
        for row in rows:
            if 'error' in row:
                failures.append(row)
                continue
            try:
                proposed, missing = pairs_at_cutoff(row, cutoff)
                missing_times.append({'name': row['name'], 'missing_timestamp_versions': missing,
                                      'pair_count': len(proposed)})
                active = [s for s in row['searches'] if s['inspection_rank'] <= protocol['wave_rank']]
                if active:
                    pairs.extend(dict(p, searches=active) for p in proposed)
                else:
                    deferred.extend(proposed)
            except Exception as exc:
                failures.append(dict(row, error=f'{type(exc).__name__}: {exc}'))
        write_jsonl(out / 'path-b-pairs.jsonl', pairs)
        write_jsonl(out / 'path-b-deferred-pairs.jsonl', deferred)
        write_jsonl(out / 'metadata-failures.jsonl', failures)
        write_jsonl(out / 'version-coverage.jsonl', missing_times)
        wanted = {}
        last_path, doc = None, None
        for pair in pairs:
            if pair['metadata_file'] != last_path:
                last_path = pair['metadata_file']
                doc = json.loads(Path(last_path).read_text())
            for version in (pair['before'], pair['after']):
                wanted[(pair['name'], version)] = dict(name=pair['name'], version=version,
                    dist=doc['versions'][version]['dist'], metadata_file=pair['metadata_file'],
                    metadata_sha256=pair['metadata_sha256'])
        write_jsonl(out / 'wanted.path-b.jsonl', wanted.values())
        print(json.dumps({'pairs': len(pairs), 'versions': len(wanted), 'deferred_pairs': len(deferred)}))
    else:
        wanted = load_jsonl(out / 'wanted.path-b.jsonl')
        errors = 0
        with ThreadPoolExecutor(max_workers=args.workers) as executor, (out / 'archives.jsonl').open('w') as stream:
            for index, row in enumerate(executor.map(lambda r: fetch_archive(r, cache / 'tarballs'), wanted), 1):
                stream.write(json.dumps(row) + '\n')
                stream.flush()
                errors += 'error' in row
                if index % 50 == 0 or index == len(wanted):
                    print(json.dumps({'archives': index, 'total': len(wanted), 'errors': errors}), flush=True)


if __name__ == '__main__':
    main()
