"""Audit the cached candidate pool: python pipeline/expansion_inventory.py --out DIR."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from samples import load_jsonl
from wyss import write_jsonl


def sha256(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def exposure_inventory(root):
    paths = [root / 'evaluation/full-method-20261012/pairs.jsonl']
    paths += sorted((root / 'evaluation').glob('*/dev-exclusions.jsonl'))
    paths += sorted((root / 'evaluation').glob('*/retrieval-exclusions.jsonl'))
    exposed = {}
    for path in paths:
        for row in load_jsonl(path):
            identity = row.get('id', row.get('pair_id'))
            name = row.get('name') or exposed.get(identity, {}).get('name')
            if not identity or not name:
                raise ValueError(f'Missing exposure identity: {path}')
            entry = exposed.setdefault(identity, {'id': identity, 'name': name,
                                                  'sources': [], 'related_names': []})
            entry['sources'].append(str(path))
            related = set(row.get('retrieval_exclude_names', []))
            if row.get('dependency'):
                related.add(row['dependency'])
            related.update(x['dependency'] for x in
                           row.get('delta_evidence', {}).get('dependency_change', []))
            entry['related_names'] = sorted(set(entry['related_names']) | related)
    return list(exposed.values()), paths


def screen_typical(rows, extracted, advisory, exposures, hn_ids):
    ids = {r['id'] for r in exposures}
    names = {r['name'] for r in exposures}
    related = {n for r in exposures for n in r['related_names']}
    accepted, rejected = [], []
    for row in rows:
        keys = [(row['name'], row[side]) for side in ('before', 'after')]
        versions = [extracted.get(k, {}) for k in keys]
        checks = [advisory.get(k) for k in keys]
        reasons = []
        if any(not v or v.get('error') for v in versions):
            reasons.append('version_unavailable_or_invalid')
        if any(c is None for c in checks):
            reasons.append('advisory_check_missing')
        elif any(c['has_advisory'] for c in checks):
            reasons.append('advisory_present')
        entry = dict(row, annotation_status='pending', gold_label=None,
                     assumed_label='benign', label_basis='Wyss typical assumption',
                     advisory_checks=checks, overlaps_hn=row['id'] in hn_ids,
                     pair_exposed=row['id'] in ids,
                     package_exposed=row['name'] in names,
                     related_dependency_exposed=row['name'] in related,
                     holdout_eligible=False, clone_check_status='pending')
        if reasons:
            rejected.append(dict(entry, reasons=reasons))
            continue
        accepted.append(dict(entry, before_dir=versions[0]['dir'],
                             after_dir=versions[1]['dir'],
                             sha256_before=versions[0]['sha256'],
                             sha256_after=versions[1]['sha256']))
    return accepted, rejected


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    root, out = Path('data/acquisition'), Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    exposures, paths = exposure_inventory(Path('data'))
    write_jsonl(out / 'exposure-registry.jsonl', exposures)
    inputs = ['typ.draw.jsonl', 'typ.pool.jsonl', 'extracted.typical.jsonl',
              'advisories.jsonl', 'hn.candidates.jsonl', 'samples.typical.jsonl',
              'pairs.preprocessed-v2.jsonl']
    paths += [root / name for name in inputs]
    rows = load_jsonl(root / inputs[0]) + load_jsonl(root / inputs[1])
    if len({r['id'] for r in rows}) != len(rows):
        raise ValueError('Duplicate source pair identities')
    extracted = {(r['name'], r['version']): r for r in load_jsonl(root / inputs[2])}
    downloads = {(r['name'], r['version']): r for r in load_jsonl(root / inputs[5])}
    for key, row in extracted.items():
        if row.get('error'):
            continue
        try:
            manifest = json.loads((Path(row['dir']) / 'package.json').read_text())
            assert manifest['name'] == key[0]
            assert manifest['version'].split('+')[0] == key[1].split('+')[0]
            assert sha256(downloads[key]['tarball']) == row['sha256']
        except (OSError, KeyError, ValueError, AssertionError):
            row['error'] = 'cached_identity_or_archive_verification_failed'
    advisory = {(r['name'], r['version']): r for r in load_jsonl(root / inputs[3])}
    hn = {r['id'] for r in load_jsonl(root / inputs[4])}
    accepted, rejected = screen_typical(rows, extracted, advisory, exposures, hn)
    write_jsonl(out / 'typical-candidates.jsonl', accepted)
    write_jsonl(out / 'typical-exclusions.jsonl', rejected)
    queue = [r for r in accepted if not any(r[k] for k in
             ('pair_exposed', 'package_exposed', 'related_dependency_exposed'))]
    write_jsonl(out / 'typical-unexposed-review-queue.jsonl', queue)
    mal = [r for r in load_jsonl(root / inputs[6]) if r['subset'] == 'MAL']
    # Campaign assignments come from the frozen evaluated inputs, not predictions.
    baseline = load_jsonl(Path('data/evaluation/full-method-20261012/pairs.jsonl'))
    campaigns = Counter(r['campaign'] for r in baseline if r['subset'] == 'MAL')
    summary = dict(source_pairs=len(rows), available_typical_candidates=len(accepted),
                   exclusions=len(rejected), exclusion_reasons=dict(Counter(
                       x for r in rejected for x in r['reasons'])),
                   groups=dict(Counter(r['group'] for r in accepted)),
                   already_inferred_pairs=sum(r['pair_exposed'] for r in accepted),
                   hn_overlap=sum(r['overlaps_hn'] for r in accepted),
                   unexposed_by_identity_review_queue=len(queue),
                   final_holdout_pairs=0, human_labels_created=0,
                   advisory_check_dates=sorted({c['checked_at'][:10] for r in accepted
                                                for c in r['advisory_checks']}),
                   mal_preprocessed=len(mal), mal_evaluated=sum(campaigns.values()),
                   mal_clusters=len(campaigns), largest_mal_cluster=max(campaigns.values()),
                   mal_capacity_with_cap3=sum(min(n, 3) for n in campaigns.values()),
                   note='Cached advisory checks; all candidates require final split and review.')
    (out / 'inventory-summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    pins = {str(p): {'sha256': sha256(p), 'bytes': p.stat().st_size} for p in paths}
    (out / 'input-manifest.json').write_text(json.dumps(pins, indent=2) + '\n')
    print(json.dumps(summary), flush=True)


if __name__ == '__main__':
    main()
