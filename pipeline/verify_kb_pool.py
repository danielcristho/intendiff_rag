"""Verify the full pinned malicious-intent pool and report explicit exclusions.

    python pipeline/verify_kb_pool.py --acquisition data/acquisition
"""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from samples import load_jsonl


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--acquisition', required=True)
    args = parser.parse_args()
    root = Path(args.acquisition)
    pool_path = root / 'datadog.intent-full.pool.jsonl'
    fetch_path = root / 'datadog.intent-full.jsonl'
    inventory_path = root / 'datadog.inventory-full.jsonl'
    pool = load_jsonl(pool_path)
    downloaded = load_jsonl(fetch_path)
    expected = {row['id']: row for row in pool}
    acquired = {row['id']: row for row in downloaded}
    assert len(expected) == len(pool) == len(downloaded) == len(acquired)
    assert expected.keys() == acquired.keys(), 'download coverage differs from pinned pool'
    inventory = {row['id']: row for row in load_jsonl(inventory_path)
                 if row['kind'] == 'malicious_intent'}
    assert inventory.keys() == expected.keys(), 'inventory coverage differs from pinned pool'
    advisories = {(row['name'], row['version']): row
                  for row in load_jsonl(root / 'campaign-advisories-full.jsonl')}
    errors = []
    for index, (key, row) in enumerate(acquired.items(), 1):
        assert not row.get('error'), f'download requires retry: {key}: {row.get("error")}'
        original, extracted = expected[key], inventory[key]
        for field in ('name', 'version', 'git_blob_sha1', 'bytes'):
            assert row[field] == original[field], (key, field)
            assert extracted[field] == original[field], (key, field)
        archive = Path(row['archive'])
        size = archive.stat().st_size
        assert size == original['bytes'], key
        sha256 = hashlib.sha256()
        git_sha1 = hashlib.sha1(f'blob {size}\0'.encode())
        with archive.open('rb') as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b''):
                sha256.update(chunk)
                git_sha1.update(chunk)
        assert sha256.hexdigest() == row['sha256'] == extracted['sha256'], key
        assert git_sha1.hexdigest() == original['git_blob_sha1'], key
        assert (row['name'], row['version']) in advisories, key
        if extracted.get('error'):
            errors.append({'id': key, 'error': extracted['error']})
        else:
            assert Path(extracted['dir']).is_dir(), key
            assert extracted['annotation_status'] == 'pending', key
        if index % 1000 == 0:
            print(f'verified {index}/{len(pool)}', flush=True)
    summary = {'scope': 'Full pinned Datadog malicious-intent version pool',
               'revision': next(iter(acquired.values()))['revision'],
               'pool': len(pool), 'verified_archives': len(acquired),
               'archive_bytes': sum(r['bytes'] for r in pool),
               'valid_inventory': len(inventory) - len(errors),
               'inventory_exclusions': len(errors),
               'exclusion_reasons': dict(Counter(r['error'] for r in errors)),
               'errors': errors, 'final_cards_selected': False,
               'input_sha256': {str(p): digest(p) for p in (pool_path, fetch_path, inventory_path)}}
    (root / 'kb-pool-verification.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({key: value for key, value in summary.items() if key != 'errors'}), flush=True)


if __name__ == '__main__':
    main()
