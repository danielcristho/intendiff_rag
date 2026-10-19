"""Usage: python pipeline/campaign_audit_evidence.py --audit DIR --review FILE FILE."""
import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from types import SimpleNamespace

from campaign_materials import acquisition_rows, review_rows
from samples import load_jsonl
from wyss import write_jsonl


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--audit', required=True)
    parser.add_argument('--review', required=True, nargs='+')
    args = parser.parse_args()
    root = Path(args.audit)
    if (root / 'hash-source-examples.jsonl').exists():
        raise ValueError('Source evidence already exists')
    items = {r['id']: r for r in load_jsonl(root / 'material-index.jsonl')}
    edges = load_jsonl(root / 'witness-forest.jsonl')
    paths = load_jsonl(root / 'dev-exposure-paths.jsonl')
    selected_hashes = {r['sha256'] for r in load_jsonl(root / 'giant-common-hashes.jsonl')}
    counts = Counter(digest for row in items.values() for digest in row['added_hashes'])
    review_hashes = {digest for row in items.values() if row['role'].startswith('review_')
                     for digest in row['added_hashes']}
    selected_hashes.update(digest for digest in review_hashes if counts[digest] > 30)
    # Include every exact-file bridge in the exclusion paths, not just frequent files.
    selected_hashes.update(edges[i]['value'] for row in paths for i in row['edge_indices']
                           if edges[i]['criterion'] == 'added_hashes')
    members = defaultdict(list)
    for identity, row in items.items():
        for digest in set(row['added_hashes']) & selected_hashes:
            members[digest].append(identity)
    wanted = defaultdict(set)
    for digest, identities in members.items():
        for identity in sorted(identities, key=lambda key: (not items[key]['role'].startswith('review_'), key))[:2]:
            wanted[identity].add(digest)
    sources = list(acquisition_rows(SimpleNamespace(
        acquisition='data/acquisition', inventory='datadog.inventory-full.jsonl',
        advisories='campaign-advisories-full.jsonl'))) + list(review_rows(args.review))
    rows = []
    for identity, role, before, after, _ in sources:
        if identity not in wanted:
            continue
        existing = {p.relative_to(before).as_posix() for p in before.rglob('*') if p.is_file()} if before else set()
        found = set()
        for path in sorted(after.rglob('*')):
            if not path.is_file() or path.relative_to(after).as_posix() in existing:
                continue
            raw = path.read_bytes()
            digest = hashlib.sha256(raw).hexdigest()
            if digest not in wanted[identity] or digest in found:
                continue
            found.add(digest)
            rows.append(dict(id=identity, role=role, sha256=digest, source_path=str(path),
                             relative_path=path.relative_to(after).as_posix(), bytes=len(raw),
                             stripped_bytes=len(raw.strip()), member_count=len(members[digest]),
                             preview=raw[:300].decode('utf-8', errors='replace')))
        if found != wanted[identity]:
            raise ValueError(f'Missing source hash in {identity}: {wanted[identity] - found}')
    expected = sum(map(len, wanted.values()))
    if len(rows) != expected:
        raise ValueError(f'Only {len(rows)} of {expected} requested file examples found')
    write_jsonl(root / 'hash-source-examples.jsonl', rows)
    usage = Counter(i for row in paths for i in row['edge_indices'])
    bridges = [dict(edge_index=i, exclusion_paths=count, **edges[i])
               for i, count in usage.most_common() if edges[i]['criterion'] == 'dolos']
    write_jsonl(root / 'dev-dolos-bridges.jsonl', bridges)
    campaign_root = Path('data/acquisition/campaigns-20261013')
    frozen = json.loads((campaign_root / 'combined-d96.json').read_text())
    exclusions = []
    for row in load_jsonl(campaign_root / 'split-proposal.jsonl'):
        if row['holdout_eligible'] and row['campaign_roles'].get('kb_pool'):
            exclusions.append(dict(id=row['id'], campaign=row['campaign'], exclude_kb_ids=[
                key for key, group in frozen['campaigns'].items()
                if group == row['campaign'] and frozen['item_roles'][key] == 'kb_pool'],
                status='required when constructing final retrieval inputs; not applied to historical runs'))
    write_jsonl(root / 'holdout-kb-exclusions.jsonl', exclusions)
    print(json.dumps(dict(source_hashes=len(selected_hashes), verified_file_examples=len(rows),
                          dev_dolos_bridges=len(bridges))))


if __name__ == '__main__':
    main()
