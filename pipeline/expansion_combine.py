"""Combine screened candidate strata without assigning gold labels or final splits."""
import argparse
import json
from collections import Counter
from pathlib import Path

from samples import load_jsonl
from wyss import write_jsonl


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True)
    parser.add_argument('--inventory', required=True)
    parser.add_argument('--stream', required=True)
    args = parser.parse_args()
    out, first, stream = Path(args.out), Path(args.inventory), Path(args.stream)
    checks = {(r['name'], r['version']): r for r in
              load_jsonl(first / 'typical-advisories.jsonl') + load_jsonl(out / 'advisories.jsonl')}
    exposures = load_jsonl(first / 'exposure-registry.jsonl')
    ids = {r['id'] for r in exposures}
    names = {r['name'] for r in exposures}
    dependencies = {n for r in exposures for n in r['related_names']}

    def unexposed(row):
        return row['id'] not in ids and row['name'] not in names | dependencies

    old, excluded = [], []
    original = load_jsonl('data/acquisition/hn.candidates.jsonl')
    for row in original:
        current = [checks.get((row['name'], row[s])) for s in ('before', 'after')]
        reasons = []
        if not row['same_publisher']:
            reasons.append('publisher_changed_or_missing')
        if any(c is None for c in current):
            reasons.append('fresh_advisory_check_missing')
        elif any(c['has_advisory'] for c in current):
            reasons.append('advisory_present')
        entry = dict(row, advisory_checks=current, gold_label=None, annotation_status='pending',
                     holdout_eligible=False, clone_check_status='pending', documented_purpose_verified=False,
                     pair_exposed=row['id'] in ids, package_exposed=row['name'] in names,
                     related_dependency_exposed=row['name'] in dependencies, review_source='original-path-a')
        if reasons:
            excluded.append(dict(entry, reasons=reasons))
        else:
            old.append(entry)
    new = [dict(r, review_source='path-b-expansion') for r in load_jsonl(out / 'review.hn.jsonl')]
    hn = old + new
    typical = load_jsonl(out / 'review.typical.jsonl') + load_jsonl(stream / 'review.typical.jsonl')
    assert len({r['id'] for r in hn}) == len(hn)
    assert len({r['id'] for r in typical}) == len(typical)
    assert all(r['gold_label'] is None and not r['holdout_eligible'] for r in typical + hn)
    assert not {r['name'] for r in load_jsonl(stream / 'review.typical.jsonl')} & (
        names | dependencies | {r['name'] for r in hn})
    write_jsonl(out / 'review.hn-combined.jsonl', hn)
    write_jsonl(out / 'review.typical-combined.jsonl', typical)
    write_jsonl(out / 'original-hn-current-exclusions.jsonl', excluded)
    for annotator in ('A', 'B'):
        path = out / f'annotation-template.combined.{annotator}.jsonl'
        if not path.exists():
            write_jsonl(path, [dict(id=r['id'], annotator=annotator, label=None, category=None,
                purpose_evidence=[], malicious_evidence=[], notes='', status='pending') for r in hn])
        assert {r['id'] for r in load_jsonl(path)} == {r['id'] for r in hn}
    summary = dict(typical_candidate_pairs=len(typical),
                   typical_strata=dict(Counter(r['group'] for r in typical)),
                   typical_unexposed_by_identity=sum(unexposed(r) for r in typical),
                   hn_original_prefilter_passed=len(old), hn_new_prefilter_passed=len(new),
                   hn_combined_prefilter_passed=len(hn),
                   hn_total_raw_candidates=len({r['id'] for r in original + load_jsonl(out / 'hn-candidates.jsonl')}),
                   hn_unexposed_by_identity=sum(unexposed(r) for r in hn),
                   typical_hn_overlap=len({r['id'] for r in typical} & {r['id'] for r in hn}),
                   distinct_typical_hn_review_pairs=len({r['id'] for r in typical + hn}),
                   gold_labels_created=0, final_holdout_pairs=0, new_mal_pairs=0, new_inferences=0)
    (out / 'combined-readiness.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
