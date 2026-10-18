"""Usage: python pipeline/external_mal_targets.py --out DIR (offline container)."""
import argparse
import hashlib
import json
import stat
import zipfile
from pathlib import Path, PurePosixPath

from expansion_screen import inspect_archive
from samples import load_jsonl
from wyss import write_jsonl

MAX_ARCHIVE = 128 * 1024 * 1024


def target_identity(member, wanted):
    parts = PurePosixPath(member.filename).parts
    if len(parts) != 6 or parts[:3] != ('NPMStudy', 'Dataset', 'zip_malware'):
        return None
    identity = (parts[3].replace('##', '/'), parts[4])
    if identity not in wanted or not parts[-1].endswith(('.tgz', '.tar.gz')):
        return None
    mode = member.external_attr >> 16
    if stat.S_ISLNK(mode) or member.file_size > MAX_ARCHIVE or member.is_dir():
        raise ValueError(f'Unsafe target member: {member.filename}')
    return identity


def collect(archives, candidates, out):
    wanted = {(r['name'], r['after']) for r in candidates}
    found = {identity: [] for identity in wanted}
    pins = []
    blobs = out / 'archives'
    blobs.mkdir()
    for archive in archives:
        path = Path(archive['path'])
        with path.open('rb') as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        if digest != archive['sha256']:
            raise ValueError(f'Source archive changed: {path}')
        pins.append(dict(path=str(path), sha256=digest))
        with zipfile.ZipFile(path) as source:
            for member in source.infolist():
                identity = target_identity(member, wanted)
                if identity is None:
                    continue
                with source.open(member) as stream:
                    raw = stream.read(MAX_ARCHIVE + 1)
                if len(raw) > MAX_ARCHIVE or len(raw) != member.file_size:
                    raise ValueError(f'Target size mismatch: {member.filename}')
                sha = hashlib.sha256(raw).hexdigest()
                target = blobs / (sha + '.tgz')
                if not target.exists():
                    target.write_bytes(raw)
                found[identity].append(dict(tarball=str(target), sha256=sha,
                    source_archive=str(path), source_archive_sha256=digest, member=member.filename))
        print(json.dumps(dict(indexed=str(path), targets_found=sum(bool(v) for v in found.values()))), flush=True)
    rows = []
    for (name, version), matches in sorted(found.items()):
        row = dict(name=name, version=version, matches=matches)
        hashes = {m['sha256'] for m in matches}
        if len(hashes) != 1:
            row['error'] = 'missing_target' if not hashes else 'conflicting_source_archives'
        else:
            row.update(matches[0])
        rows.append(row)
    return rows, pins


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--candidates', type=Path, default=Path('data/acquisition/external-mal-20261014/pair-candidates.jsonl'))
    parser.add_argument('--archive-pins', type=Path, default=Path('data/preparation/final-rag-20261014/external-archive-verification.json'))
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    archives = [r for r in json.loads(args.archive_pins.read_text()) if r['path'].endswith('.zip')]
    rows, pins = collect(archives, load_jsonl(args.candidates), args.out)
    write_jsonl(args.out / 'archives.after.jsonl', rows)
    inspected = [dict(inspect_archive(r, args.out / 'extracted'), source_matches=r['matches']) for r in rows]
    write_jsonl(args.out / 'extracted.after.jsonl', inspected)
    summary = dict(candidates=len(rows), extracted=sum('error' not in r for r in inspected),
                   errors=[dict(name=r['name'], version=r['version'], error=r['error']) for r in inspected if 'error' in r],
                   archive_pins=pins, sample_execution=False)
    (args.out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == '__main__':
    main()
