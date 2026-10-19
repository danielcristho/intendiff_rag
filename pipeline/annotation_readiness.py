"""Usage: python -m pipeline.annotation_readiness --cohort PATH --annotators NAME NAME."""
import argparse
import json
import re
from collections import Counter
from pathlib import Path

from pipeline.evidence import index_diff


def decision_issues(pair, decision):
    if not isinstance(decision, dict) or decision.get('label') not in ('malicious', 'benign', 'skip'):
        return ['missing_or_invalid_label']
    issues = []
    if not isinstance(decision.get('note'), str) or not decision['note'].strip():
        issues.append('missing_rationale_and_reference')
    if decision['label'] == 'malicious':
        evidence = decision.get('gold_evidence')
        if not isinstance(evidence, list) or not evidence or not all(isinstance(x, str) for x in evidence):
            issues.append('missing_or_invalid_evidence')
        else:
            index = index_diff(pair['diff'])
            lines = {r['text'] for r in index}
            changed = {r['text'] for r in index if r['kind'] in ('added', 'deleted')}
            if any(line not in lines for line in evidence):
                issues.append('evidence_not_verbatim')
            if not changed.intersection(evidence):
                issues.append('evidence_has_no_changed_content')
    if decision['label'] == 'benign' and pair.get('subset') == 'HN':
        category = decision.get('category')
        if type(category) is not int or category not in range(1, 6):
            issues.append('missing_hn_purpose_category')
    return issues


def assess(pairs, mapping, decisions):
    if len(decisions) != 2:
        raise ValueError('Exactly two distinct annotator identities are required')
    pair_by_id = {p['id']: p for p in pairs}
    review_ids = {m['review_id'] for m in mapping}
    if len(pair_by_id) != len(pairs) or len(review_ids) != len(mapping):
        raise ValueError('Duplicate pair or review IDs')
    if {m['pair_id'] for m in mapping} != set(pair_by_id) or len(mapping) != len(pairs):
        raise ValueError('Mapping must cover the cohort exactly once')
    unexpected = {name: sorted(set(votes) - review_ids) for name, votes in decisions.items()}
    rows = []
    for entry in mapping:
        pair = pair_by_id[entry['pair_id']]
        votes = {name: votes.get(entry['review_id']) for name, votes in decisions.items()}
        issues = {name: decision_issues(pair, vote) for name, vote in votes.items()}
        state = 'incomplete'
        if not any(issues.values()):
            labels = [vote['label'] for vote in votes.values()]
            if 'skip' in labels:
                state = 'skip_requires_review'
            elif len(set(labels)) != 1:
                state = 'label_disagreement'
            elif pair['subset'] == 'HN' and labels[0] == 'benign' and len({v['category'] for v in votes.values()}) != 1:
                state = 'category_disagreement'
            else:
                state = 'agreement_requires_semantic_review'
        rows.append({'review_id': entry['review_id'], 'state': state, 'issues': issues})
    counts = dict(Counter(r['state'] for r in rows))
    return {'total': len(rows), 'annotators': list(decisions), 'counts': counts,
            'unexpected_ids': unexpected,
            'all_independent_forms_complete': bool(rows) and 'incomplete' not in counts and not any(unexpected.values()),
            'gold_ready': False, 'human_identity_and_semantic_verification_required': True,
            'rows': rows}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cohort', type=Path, required=True)
    parser.add_argument('--annotators', nargs=2, required=True)
    args = parser.parse_args()
    if len(set(args.annotators)) != 2 or not all(re.fullmatch(r'[A-Za-z0-9_-]{1,32}', n) for n in args.annotators):
        parser.error('Use two distinct identities containing only letters, digits, _ or -')
    decisions = {}
    for name in args.annotators:
        path = args.cohort / 'annotation' / f'audit_decisions.{name}.json'
        votes = json.loads(path.read_text()) if path.exists() else {}
        if not isinstance(votes, dict):
            raise ValueError(f'Expected decision object in {path}')
        decisions[name] = votes
    read = lambda name: [json.loads(line) for line in (args.cohort / name).read_text().splitlines()]
    report = assess(read('pairs.jsonl'), read('mapping.jsonl'), decisions)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
