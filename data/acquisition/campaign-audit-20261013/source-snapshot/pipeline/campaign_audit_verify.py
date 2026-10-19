"""Usage: python pipeline/campaign_audit_verify.py --audit DIR."""
import argparse
import hashlib
import json
from pathlib import Path

from campaign import find, union
from campaign_audit import Fingerprints
from campaign_fingerprints import similarity
from expansion_split import exposed_members, merge_review
from samples import load_jsonl


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--audit', required=True)
    args = parser.parse_args()
    out = Path(args.audit)
    pins = load_jsonl(out / 'input-pins.jsonl')
    for row in pins:
        with Path(row['path']).open('rb') as stream:
            observed = hashlib.file_digest(stream, 'sha256').hexdigest()
        if observed != row['sha256']:
            raise ValueError(f"Changed input: {row['path']}")
    frozen = json.loads(Path('data/acquisition/campaigns-20261013/combined-d96.json').read_text())
    items = {r['id']: r for r in load_jsonl(out / 'material-index.jsonl')}
    edges = load_jsonl(out / 'witness-forest.jsonl')
    parent = {key: key for key in items}
    fingerprints = Fingerprints('data/work/audit/fingerprints')
    for edge in edges:
        left, right = items[edge['left']], items[edge['right']]
        if find(parent, left['id']) == find(parent, right['id']):
            raise ValueError('Witness forest contains a cycle')
        if edge['criterion'] == 'dolos':
            score = similarity(fingerprints[left['code_key']], fingerprints[right['code_key']])
            if score != edge['score'] or score < 0.5:
                raise ValueError('Invalid Dolos witness')
        elif edge['criterion'] in ('reports', 'added_hashes'):
            if not all(edge['value'] in row[edge['criterion']] for row in (left, right)):
                raise ValueError('Invalid exact witness')
        else:
            raise ValueError('Unknown witness criterion')
        union(parent, left['id'], right['id'])
    if {key: find(parent, key) for key in parent} != frozen['campaigns']:
        raise ValueError('Witness partition differs from frozen D96')
    review = merge_review([
        'data/acquisition/expansion-full-20261013/review.typical-combined.jsonl',
        'data/acquisition/expansion-full-20261013/review.hn-combined.jsonl'])
    exposed = exposed_members(frozen['campaigns'], frozen['item_roles'], review,
                              load_jsonl('data/acquisition/expansion-full-20261013/exposure-registry.jsonl'))
    paths = load_jsonl(out / 'dev-exposure-paths.jsonl')
    for row in paths:
        current = row['id']
        for index in row['edge_indices']:
            edge = edges[index]
            if current not in (edge['left'], edge['right']):
                raise ValueError('Broken exposure path')
            current = edge['right'] if current == edge['left'] else edge['left']
        if current != row['exposed_item'] or current not in exposed:
            raise ValueError('Exposure path has no independently identified exposed endpoint')
    result = dict(input_hashes_verified=len(pins), witness_edges_verified=len(edges),
                  exclusion_paths_verified=len(paths), frozen_partition_reproduced=True,
                  cross_partition_dolos_edges_rechecked=False)
    (out / 'verification.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
