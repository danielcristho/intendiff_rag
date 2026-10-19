"""Usage: python pipeline/final_readiness.py --out REPORT.json [--pairs FILE --kb FILE]."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from configs import CONFIGS, CONTRASTS
from retrieval_audit import audit_retrieval
from runner import retrieve
from label_provenance import validate

ROOT = Path(__file__).resolve().parents[1]


def assess(pairs, cards, exposure):
    issues = []
    subsets = Counter(r.get('subset') for r in pairs)
    for subset in ('MAL', 'TYP'):
        if not subsets[subset]:
            issues.append(dict(reason='missing_subset', subset=subset))
    if not cards:
        issues.append(dict(reason='missing_kb'))
    exposed_ids = {r['id'] for r in exposure}
    exposed_names = {r['name'] for r in exposure} | {n for r in exposure for n in r.get('related_names', [])}
    source_cache = {}
    for row in pairs:
        identity = row.get('id')
        if identity in exposed_ids or row.get('name') in exposed_names:
            issues.append(dict(id=identity, reason='development_exposure'))
        if row.get('evaluation_scope') != 'final_holdout':
            issues.append(dict(id=identity, reason='not_declared_final_holdout'))
        expected = 'malicious' if row.get('subset') == 'MAL' else 'benign'
        if row.get('label') != expected:
            issues.append(dict(id=identity, reason='missing_or_inconsistent_label'))
        source_issue = validate(row, source_cache)
        if source_issue:
            issues.append(dict(id=identity, reason=source_issue))
        if row.get('subset') not in ('MAL', 'TYP'):
            issues.append(dict(id=identity, reason='outside_source_labelled_primary_scope'))
        if row.get('subset') == 'HN' and (type(row.get('category')) is not int or row['category'] not in range(1, 6)):
            issues.append(dict(id=identity, reason='missing_hn_category'))
        if row.get('intent_from') != row.get('before') or not row.get('before'):
            issues.append(dict(id=identity, reason='intent_origin_not_verified'))
        if not row.get('diff') or row.get('preprocessing', {}).get('version') != 'static-dolos-exact-v2':
            issues.append(dict(id=identity, reason='missing_normalized_diff'))
    for card in cards:
        source_issue = validate(card, source_cache)
        if source_issue:
            issues.append(dict(id=card.get('id'), reason=source_issue))
        for field in ('source', 'intent', 'behavior_chain', 'code_excerpt', 'rationale'):
            if not isinstance(card.get(field), str) or not card[field].strip():
                issues.append(dict(id=card.get('id'), reason='missing_card_content', field=field))
    retrieval_issues, plan = audit_retrieval(pairs, cards, list(CONFIGS), retrieve)
    issues.extend(retrieval_issues)
    return dict(input_checks_passed=not issues, launch_ready=False,
                label_policy='D99_source_labelled',
                remaining_release_checks=['card excerpt provenance', 'campaign split and dependency exclusions',
                                          'card and prompt budgets for each model', 'G1/G2 and protocol/code/model/input pins'],
                pairs=len(pairs), subsets=dict(subsets), cards=len(cards),
                configurations=list(CONFIGS), contrasts=CONTRASTS,
                primary_models=['Qwen/Qwen3-4B-Instruct-2507', 'Qwen/Qwen2.5-Coder-3B-Instruct'],
                expected_stage1_generations=len(pairs) * len(CONFIGS) * 2,
                issues=issues, retrieval_plan=plan)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pairs', type=Path, default=ROOT / 'data/pairs.jsonl')
    parser.add_argument('--kb', type=Path, default=ROOT / 'data/kb.jsonl')
    parser.add_argument('--exposure', type=Path, default=ROOT / 'data/acquisition/expansion-full-20261013/exposure-registry.jsonl')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    pins, missing = [], []
    def read(path):
        if not path.is_file():
            missing.append(dict(reason='missing_input_file', path=str(path)))
            return []
        raw = path.read_bytes()
        pins.append(dict(path=str(path), sha256=hashlib.sha256(raw).hexdigest()))
        return [json.loads(line) for line in raw.splitlines() if line.strip()]
    report = assess(read(args.pairs), read(args.kb), read(args.exposure))
    report['issues'].extend(missing)
    report['input_checks_passed'] = not report['issues']
    report['input_pins'] = pins
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'retrieval_plan'}, indent=2))
    # This audit does not grant a release from boolean metadata alone.
    raise SystemExit(2)


if __name__ == '__main__':
    main()
