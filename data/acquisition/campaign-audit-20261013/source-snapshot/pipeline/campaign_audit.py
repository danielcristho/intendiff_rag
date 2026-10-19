"""Usage: python pipeline/campaign_audit.py --items FILE FILE --cache DIR --out DIR."""
import argparse
import hashlib
import json
from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path

import campaign
from campaign_audit_graph import complete_forest, exposure_paths
from expansion_split import EXPOSURE_FLAGS, exposed_members, merge_review
from samples import load_jsonl
from wyss import write_jsonl


def pin(path):
    with Path(path).open('rb') as stream:
        return dict(path=str(path), sha256=hashlib.file_digest(stream, 'sha256').hexdigest())


class Fingerprints:
    def __init__(self, directory):
        self.directory = Path(directory)

    @lru_cache(maxsize=16)
    def __getitem__(self, key):
        return json.loads((self.directory / (key + '.json')).read_bytes())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--items', nargs='+', required=True)
    parser.add_argument('--cache', required=True)
    parser.add_argument('--campaigns', required=True)
    parser.add_argument('--split', required=True)
    parser.add_argument('--review', nargs='+', required=True)
    parser.add_argument('--exposure', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    if (out / 'summary.json').exists():
        raise ValueError('Use a new directory to preserve the completed audit')
    items, pins = [], []
    for path in args.items:
        digest = hashlib.sha256()
        with Path(path).open('rb') as source:
            for line in source:
                digest.update(line)
                row = json.loads(line)
                row['code_key'] = hashlib.sha256(row.pop('code').encode()).hexdigest()
                items.append(row)
        pins.append(dict(path=path, sha256=digest.hexdigest()))
        print(json.dumps(dict(material_loaded=path, items=len(items))), flush=True)
    frozen = json.loads(Path(args.campaigns).read_text())
    if not frozen['complete_for_available_items'] or frozen['hash_rule'] != 'd96':
        raise ValueError('Expected a complete D96 campaign run')
    assigned = frozen['campaigns']
    giant, giant_size = Counter(assigned.values()).most_common(1)[0]
    giant_rows = [r for r in items if assigned[r['id']] == giant]
    ablations = {}
    for fields in (('reports',), ('added_hashes',), ('reports', 'added_hashes')):
        groups = campaign.cluster([dict(id=r['id'], **{f: r[f] for f in fields}) for r in items])
        ablations['+'.join(fields)] = dict(
            clusters=len(set(groups.values())), largest=Counter(groups.values()).most_common(10),
            giant_components=len({groups[r['id']] for r in giant_rows}),
            giant_largest_components=Counter(groups[r['id']] for r in giant_rows).most_common(10))
    write_jsonl(out / 'material-index.jsonl', items)
    fingerprints = Fingerprints(args.cache)
    for key in sorted({r['code_key'] for r in items}):
        path = Path(args.cache) / (key + '.json')
        raw = path.read_bytes()
        parsed = json.loads(raw)
        if sum(parsed['counts'].values()) != parsed['total']:
            raise ValueError(f'Invalid fingerprint counts: {path}')
        pins.append(dict(path=str(path), sha256=hashlib.sha256(raw).hexdigest()))
    del raw, parsed
    print(json.dumps(dict(fingerprint_files_verified=len({r['code_key'] for r in items}))), flush=True)
    edges, comparisons = complete_forest(
        items, assigned, fingerprints, lambda r: print(json.dumps(r), flush=True))
    write_jsonl(out / 'witness-forest.jsonl', edges)
    review = merge_review(args.review)
    exposed = exposed_members(assigned, frozen['item_roles'], review, load_jsonl(args.exposure))
    split = load_jsonl(args.split)
    targets = {r['id'] for r in split if 'campaign_with_exposed_item' in r['dev_reasons']
               and not any(review[r['id']][f] for f in EXPOSURE_FLAGS)}
    paths = exposure_paths(edges, exposed, targets)
    write_jsonl(out / 'dev-exposure-paths.jsonl', paths)
    shared = defaultdict(list)
    for row in giant_rows:
        for digest in row['added_hashes']:
            shared[digest].append(row['id'])
    top = sorted(shared, key=lambda key: (-len(shared[key]), key))[:30]
    write_jsonl(out / 'giant-common-hashes.jsonl', [
        dict(sha256=key, member_count=len(shared[key]), example_ids=sorted(shared[key])[:5]) for key in top])
    summary = dict(
        status='diagnostic only; frozen D96 split unchanged', items=len(items),
        clusters=len(set(assigned.values())), giant=giant, giant_size=giant_size,
        giant_roles=dict(Counter(r['role'] for r in giant_rows)), exact_ablations=ablations,
        witness_edges=dict(Counter(e['criterion'] for e in edges)),
        giant_witness_edges=dict(Counter(e['criterion'] for e in edges if assigned[e['left']] == giant)),
        dolos_comparisons=comparisons, frozen_partition_reproduced=True,
        certificate_limit='Proves connectivity within frozen groups; does not recheck omitted cross-group Dolos edges.',
        newly_dev_paths=len(paths), paths_requiring_dolos=sum(
            any(edges[i]['criterion'] == 'dolos' for i in r['edge_indices']) for r in paths),
        gold_labels_created=0, inferences=0, split_changes=0)
    for path in [args.campaigns, args.split, args.exposure, *args.review,
                 'pipeline/campaign.py', 'pipeline/campaign_fingerprints.py', __file__,
                 'pipeline/campaign_audit_graph.py']:
        pins.append(pin(path))
    write_jsonl(out / 'input-pins.jsonl', pins)
    (out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == '__main__':
    main()
