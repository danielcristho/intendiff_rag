"""Reconcile expanded candidates, current advisory checks and review readiness."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from samples import load_jsonl
from wyss import write_jsonl


def hn_reasons(row, checks):
    reasons = []
    if not row['same_publisher']:
        reasons.append('publisher_changed_or_missing')
    if row['earlier_unavailable_pairs']:
        reasons.append('earliest_pair_selection_incomplete')
    if any(c is None for c in checks):
        reasons.append('advisory_check_missing')
    elif any(c['has_advisory'] for c in checks):
        reasons.append('advisory_present')
    return reasons


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True)
    parser.add_argument('--inventory', required=True)
    args = parser.parse_args()
    out, first = Path(args.out), Path(args.inventory)
    paths = [first / 'typical-advisories.jsonl', out / 'advisories.jsonl']
    checks = {}
    for path in paths:
        for row in load_jsonl(path):
            key = row['name'], row['version']
            if key not in checks or row['checked_at'] > checks[key]['checked_at']:
                checks[key] = row
    exposures = load_jsonl(first / 'exposure-registry.jsonl')
    ids = {r['id'] for r in exposures}
    names = {r['name'] for r in exposures}
    dependencies = {n for r in exposures for n in r['related_names']}
    requested = {(r['name'], r[s]) for filename in
                 (first / 'typical-candidates.jsonl', out / 'hn-candidates.jsonl')
                 for r in load_jsonl(filename) for s in ('before', 'after')}
    missing = requested - checks.keys()
    if missing:
        raise ValueError(f'Advisory coverage is incomplete for {len(missing)} versions')
    typical, typ_excluded = [], []
    for row in load_jsonl(first / 'typical-candidates.jsonl'):
        current = [checks.get((row['name'], row[s])) for s in ('before', 'after')]
        reasons = []
        if any(c is None for c in current):
            reasons.append('advisory_check_missing')
        elif any(c['has_advisory'] for c in current):
            reasons.append('advisory_present')
        entry = dict(row, subset='TYP', advisory_checks=current)
        if reasons:
            typ_excluded.append(dict(entry, reasons=reasons))
        else:
            typical.append(entry)
    hn, hn_excluded = [], []
    for row in load_jsonl(out / 'hn-candidates.jsonl'):
        current = [checks.get((row['name'], row[s])) for s in ('before', 'after')]
        entry = dict(row, advisory_checks=current, pair_exposed=row['id'] in ids,
                     package_exposed=row['name'] in names,
                     related_dependency_exposed=row['name'] in dependencies,
                     documented_purpose_verified=False, clone_check_status='pending')
        reasons = hn_reasons(row, current)
        if reasons:
            hn_excluded.append(dict(entry, reasons=reasons))
        else:
            hn.append(entry)
    write_jsonl(out / 'review.typical.jsonl', typical)
    write_jsonl(out / 'review.hn.jsonl', hn)
    write_jsonl(out / 'typical-current-exclusions.jsonl', typ_excluded)
    write_jsonl(out / 'hn-screen-exclusions.jsonl', hn_excluded)
    unexposed = [r for r in typical if not any(r[k] for k in
                 ('pair_exposed', 'package_exposed', 'related_dependency_exposed'))]
    write_jsonl(out / 'typical-unexposed-review-queue.jsonl', unexposed)
    archives = load_jsonl(out / 'archives.jsonl')
    scans = load_jsonl(out / 'version-scans.jsonl')
    pair_plan = load_jsonl(out / 'path-b-pairs.jsonl')
    screened = load_jsonl(out / 'path-b-screened.jsonl')
    archive_map = {(r['name'], r['version']): r for r in archives}
    scan_map = {(r['name'], r['version']): r for r in scans}
    wanted = {(r['name'], r['version']) for r in load_jsonl(out / 'wanted.path-b.jsonl')}
    assert len(archive_map) == len(archives) == len(wanted)
    assert len(scan_map) == len(scans) == len(wanted)
    assert wanted == set(archive_map) == set(scan_map)
    assert {r['id'] for r in pair_plan} == {r['id'] for r in screened}
    assert len(pair_plan) == len(screened) == len({r['id'] for r in screened})
    for key, scan in scan_map.items():
        if 'error' not in scan:
            assert scan['sha256'] == archive_map[key]['sha256']
    for row in typical + hn:
        assert row['gold_label'] is None and not row['holdout_eligible']
        assert all(c is not None and not c['has_advisory'] for c in row['advisory_checks'])
    metadata = [r for r in load_jsonl(out / 'metadata.jsonl') if 'error' not in r]
    for row in metadata:
        assert hashlib.sha256(Path(row['metadata_file']).read_bytes()).hexdigest() == row['metadata_sha256']
    failed = [r for r in scans if 'error' in r]
    old_hn = load_jsonl('data/acquisition/hn.candidates.jsonl')
    new_hn = load_jsonl(out / 'hn-candidates.jsonl')
    new_hn_ids = {r['id'] for r in new_hn}
    original_typ_ids = {r['id'] for r in load_jsonl('data/acquisition/typ.selected.jsonl')}
    combined = {r['id']: r for r in old_hn + new_hn}
    write_jsonl(out / 'hn-combined-candidate-index.jsonl', [dict(
        id=r['id'], name=r['name'], delta=r['delta'], annotation_status='pending',
        provenance='path-b-expansion' if r['id'] in new_hn_ids else 'original-path-a'
    ) for r in combined.values()])
    summary = dict(
        typical_available_at_old_check=len(load_jsonl(first / 'typical-candidates.jsonl')),
        typical_after_current_check=len(typical), typical_new_exclusions=len(typ_excluded),
        typical_groups=dict(Counter(r['group'] for r in typical)),
        typical_not_in_original_100=sum(r['id'] not in original_typ_ids for r in typical),
        typical_gap_to_2000=max(0, 2000-len(typical)),
        typical_unexposed_identity_queue=len(unexposed),
        typical_overlap_original_hn=sum(r['overlaps_hn'] for r in typical),
        path_b_source_packages=len(load_jsonl(out / 'path-b-package-queue.jsonl')),
        path_b_pair_packages=len({r['name'] for r in pair_plan}),
        path_b_pairs=len(pair_plan), versions=len(wanted),
        downloaded_versions=sum('error' not in r for r in archives),
        downloaded_bytes=sum(r.get('bytes', 0) for r in archives),
        scanned_versions=len(scans) - len(failed), scan_failures=len(failed),
        scan_failure_reasons=dict(Counter(r['error'] for r in failed)),
        available_pairs=sum(r['screen_status'] == 'complete' for r in screened),
        hn_candidate_pairs=len(new_hn), hn_prefilter_passed=len(hn),
        hn_prefilter_rejection_reasons=dict(Counter(x for r in hn_excluded for x in r['reasons'])),
        hn_signal_categories={str(n): sum(n in r['signal_categories'] for r in hn) for n in range(1, 6)},
        hn_runtime_signal_pairs=sum(bool(set(r['delta']) & {'network', 'process_exec', 'install_script',
            'dynamic_code', 'obfuscation'}) for r in hn),
        hn_documentation_files_present=sum(bool(r['purpose_documents_before'] or r['purpose_documents_after']) for r in hn),
        hn_unexposed_identity_queue=sum(not any(r[k] for k in
            ('pair_exposed', 'package_exposed', 'related_dependency_exposed')) for r in hn),
        hn_combined_candidate_pairs=len(combined), hn_original_candidates=len(old_hn),
        human_labels_created=0, final_holdout_pairs=0, new_llm_inferences=0,
        coverage_verified=True,
        advisory_check_dates=sorted({c['checked_at'][:10] for r in typical + hn for c in r['advisory_checks']}))
    (out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    for annotator in ('A', 'B'):
        path = out / f'annotation-template.{annotator}.jsonl'
        if not path.exists():
            write_jsonl(path, [dict(id=r['id'], annotator=annotator, label=None, category=None,
                purpose_evidence=[], malicious_evidence=[], notes='', status='pending') for r in hn])
    print(json.dumps(summary), flush=True)


if __name__ == '__main__':
    main()
