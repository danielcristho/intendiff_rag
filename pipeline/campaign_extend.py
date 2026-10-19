"""Usage: python pipeline/campaign_extend.py --pairs FILE --out DIR (offline)."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from campaign import find, union
from campaign_fingerprints import similarity
from campaign_materials import material
from samples import load_jsonl
from wyss import write_jsonl


def extend(old, added, assigned, lookup):
    if len({r['id'] for r in old + added}) != len(old) + len(added):
        raise ValueError('Duplicate campaign item IDs')
    parent = {r['id']: r['id'] for r in old + added}
    for identity, root in assigned.items():
        union(parent, identity, root)
    owners, edges = {}, []
    for row in old + added:
        for field in ('reports', 'added_hashes'):
            for value in row.get(field, []):
                owner = owners.setdefault((field, value), row['id'])
                if find(parent, owner) != find(parent, row['id']):
                    edges.append(dict(left=owner, right=row['id'], criterion=field, value=value))
                    union(parent, owner, row['id'])
    # Every new-to-old and new-to-new score is checked; old closure is inherited.
    representatives = {}
    for row in old:
        representatives.setdefault(row['code_key'], row)
    for left in added:
        for right in representatives.values():
            score = lookup(left['code_key'], right['code_key'])
            if score >= 0.5:
                if find(parent, left['id']) != find(parent, right['id']):
                    edges.append(dict(left=left['id'], right=right['id'], criterion='dolos', score=score))
                union(parent, left['id'], right['id'])
        representatives.setdefault(left['code_key'], left)
    return {key: find(parent, key) for key in parent}, edges


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pairs', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--advisories', type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    audit = Path('data/acquisition/campaign-audit-20261013')
    index = audit / 'material-index.jsonl'
    frozen = Path('data/acquisition/campaigns-20261013/combined-d96.json')
    cache = Path('data/work/audit/fingerprints')
    pins = []
    for path in (index, frozen, args.pairs, args.advisories):
        pins.append(dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    old = load_jsonl(index)
    assigned = json.loads(frozen.read_text())['campaigns']
    if set(assigned) != {r['id'] for r in old}:
        raise ValueError('Old campaign IDs differ from material index')
    added, fingerprints = [], {}
    advisories = {(r['name'], r['version']): r for r in load_jsonl(args.advisories)}
    for pair in load_jsonl(args.pairs):
        check = advisories[(pair['name'], pair['after'])]
        if check.get('error') or 'advisory_ids' not in check:
            raise ValueError('Missing target advisory check')
        reports = [key for key in check['advisory_ids'] if key.startswith('MAL-')]
        row = material(pair['id'], 'external_mal_candidate', Path(pair['before_dir']), Path(pair['after_dir']), reports)
        key = hashlib.sha256(row['code'].encode()).hexdigest()
        request = args.out / 'fingerprint-request.json'
        request.write_text(json.dumps(dict(code=row.pop('code'))))
        parsed = subprocess.run(['dolos-fingerprints', str(request)], capture_output=True,
                                text=True, check=True, timeout=180)
        fingerprint = json.loads(parsed.stdout)
        if sum(fingerprint['counts'].values()) != fingerprint['total']:
            raise ValueError('Invalid new fingerprints')
        fingerprints[key] = fingerprint
        (args.out / (key + '.json')).write_text(json.dumps(fingerprint) + '\n')
        added.append(dict(row, code_key=key))
    write_jsonl(args.out / 'added-materials.jsonl', added)
    scores = {}
    for index, key in enumerate(sorted({r['code_key'] for r in old}), 1):
        path = cache / (key + '.json')
        raw = path.read_bytes()
        pins.append(dict(path=str(path), sha256=hashlib.sha256(raw).hexdigest()))
        fingerprint = json.loads(raw)
        for new_key, new_fingerprint in fingerprints.items():
            scores[(new_key, key)] = similarity(new_fingerprint, fingerprint)
        if index % 1000 == 0:
            print(json.dumps(dict(old_fingerprints_compared=index)), flush=True)
    def lookup(left, right):
        if (left, right) in scores:
            return scores[left, right]
        return similarity(fingerprints[left], fingerprints[right])
    result, edges = extend(old, added, assigned, lookup)
    write_jsonl(args.out / 'new-links.jsonl', edges)
    write_jsonl(args.out / 'input-pins.jsonl', pins)
    report = dict(campaigns=result, added=len(added), items=len(result), threshold=0.5,
                  inherited_old_closure=str(frozen), all_new_comparisons_checked=True,
                  old_old_comparisons_rerun=False, clusters=len(set(result.values())))
    (args.out / 'combined.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'campaigns'}), flush=True)


if __name__ == '__main__':
    main()
