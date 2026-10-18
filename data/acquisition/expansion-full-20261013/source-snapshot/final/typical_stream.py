"""Prepare and reconcile a fixed sample from Wyss's archived update-event stream."""
import argparse
import hashlib
import json
import zipfile
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

from collect import deterministic_draw, previous_version
from expansion_fetch import fetch_metadata
from samples import load_jsonl
from wyss import write_jsonl


def select_stream(lines, blocked, take):
    chosen = {}
    invalid = 0
    for identity in lines:
        name, separator, version = identity.strip().rpartition('@')
        if not separator or not name or not version:
            invalid += 1
            continue
        if name in blocked:
            continue
        score = hashlib.sha256(identity.strip().encode()).hexdigest()
        if name not in chosen or score < chosen[name]['selection_hash']:
            chosen[name] = dict(id=identity.strip(), name=name, version=version, selection_hash=score)
    selected, _ = deterministic_draw(list(chosen.values()), take, 2026, key=lambda r: r['name'])
    return selected, len(chosen), invalid


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', choices=['prepare', 'finish'])
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    out = Path(args.out)
    protocol = json.loads((out / 'protocol.json').read_text())
    if args.stage == 'finish':
        scans = load_jsonl(out / 'path-b-screened.jsonl')
        checks = {(r['name'], r['version']): r for r in load_jsonl(out / 'advisories.jsonl')}
        accepted, excluded = [], []
        for row in scans:
            advisory = [checks.get((row['name'], row[s])) for s in ('before', 'after')]
            reasons = []
            if row['screen_status'] != 'complete':
                reasons.append('archive_or_scan_unavailable')
            if any(c is None for c in advisory):
                raise ValueError('Advisory checks incomplete')
            if any(c['has_advisory'] for c in advisory):
                reasons.append('advisory_present')
            entry = dict(row, subset='TYP', group='live-stream-unseen-names',
                         assumed_label='benign', label_basis='Update-stream assumption, not human gold',
                         gold_label=None, annotation_status='pending', advisory_checks=advisory,
                         holdout_eligible=False, clone_check_status='pending')
            if reasons:
                excluded.append(dict(entry, reasons=reasons))
            else:
                accepted.append(entry)
        write_jsonl(out / 'review.typical.jsonl', accepted)
        write_jsonl(out / 'screen-exclusions.jsonl', excluded)
        summary = dict(selected_packages=len(load_jsonl(out / 'selected.jsonl')),
                       resolved_pairs=len(scans), candidates_after_checks=len(accepted),
                       excluded_after_checks=len(excluded), human_labels_created=0,
                       final_holdout_pairs=0, note='Separate stratum; do not pool FPR without specifying weights.')
        (out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
        print(json.dumps(summary))
        return
    blocked = set()
    sources = ['data/acquisition/typ.draw.jsonl', 'data/acquisition/typ.pool.jsonl',
               'data/acquisition/datadog.compromised.pool.jsonl',
               'data/acquisition/datadog.intent-full.pool.jsonl',
               'data/acquisition/expansion-full-20261013/path-b-package-queue.jsonl']
    for path in sources:
        blocked.update(r['name'] for r in load_jsonl(path))
    exposures = load_jsonl('data/acquisition/expansion-20261012/exposure-registry.jsonl')
    blocked.update(r['name'] for r in exposures)
    blocked.update(n for r in exposures for n in r['related_names'])
    archive = Path('data/upstream/wyss/replication.zip')
    with zipfile.ZipFile(archive) as zipped:
        member = next(n for n in zipped.namelist() if n.endswith('/live_analysis_update_events.txt'))
        raw = zipped.read(member)
    lines = raw.decode().splitlines()
    selected, eligible, invalid = select_stream(lines, blocked, protocol['selected_names'])
    write_jsonl(out / 'selected.jsonl', selected)
    (out / 'sampling.json').write_text(json.dumps(dict(
        source_archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(), source_member=member,
        source_member_sha256=hashlib.sha256(raw).hexdigest(), source_lines=len(lines),
        malformed_lines=invalid, excluded_known_names=len(blocked), eligible_names=eligible,
        selected_names=len(selected), seed=2026,
        source_pins={p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in sources}), indent=2) + '\n')
    cache = Path(protocol['cache']) / 'metadata'
    cache.mkdir(parents=True, exist_ok=True)
    metadata = []
    with ThreadPoolExecutor(max_workers=6) as pool, (out / 'metadata.jsonl').open('w') as stream:
        for index, row in enumerate(pool.map(lambda r: fetch_metadata(r, cache), selected), 1):
            metadata.append(row)
            stream.write(json.dumps(row) + '\n')
            stream.flush()
            if index % 50 == 0:
                print(json.dumps({'metadata': index, 'total': len(selected)}), flush=True)
    pairs, failures, wanted = [], [], {}
    for row in metadata:
        try:
            if row.get('error'):
                raise ValueError(row['error'])
            document = json.loads(Path(row['metadata_file']).read_text())
            before = previous_version(document, row['version'])
            if before is None:
                raise ValueError('No predecessor with verified publication order')
            target = datetime.fromisoformat(document['time'][row['version']].replace('Z', '+00:00'))
            if target > datetime.fromisoformat(protocol['cutoff']):
                raise ValueError('Target published after cutoff')
            for version in (before, row['version']):
                manifest = document['versions'][version]
                if (manifest.get('name'), manifest.get('version')) != (row['name'], version):
                    raise ValueError('Registry manifest identity mismatch')
                wanted[(row['name'], version)] = dict(name=row['name'], version=version,
                    dist=manifest['dist'], metadata_file=row['metadata_file'], metadata_sha256=row['metadata_sha256'])
            pairs.append(dict(id=row['id'], name=row['name'], before=before, after=row['version'],
                pair_order=1, searches=[], source='https://osf.io/92w4e/',
                source_member=member, published_before=document['time'][before],
                published_after=document['time'][row['version']],
                metadata_file=row['metadata_file'], metadata_sha256=row['metadata_sha256']))
        except Exception as exc:
            failures.append(dict(row, error=f'{type(exc).__name__}: {exc}'))
    write_jsonl(out / 'path-b-pairs.jsonl', pairs)
    write_jsonl(out / 'resolution-exclusions.jsonl', failures)
    write_jsonl(out / 'wanted.path-b.jsonl', wanted.values())
    write_jsonl(out / 'wanted.advisories.jsonl', [dict(name=n, version=v) for n, v in sorted(wanted)])
    print(json.dumps({'resolved_pairs': len(pairs), 'failures': len(failures), 'versions': len(wanted)}))


if __name__ == '__main__':
    main()
