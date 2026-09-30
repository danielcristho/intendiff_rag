"""Decompose completed budget and intent comparisons without changing verdicts."""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'data/evaluation/output-budget-20260929'
BASE = ROOT / 'data/evaluation/source-baselines-20260929'
protocol = json.loads((HERE / 'protocol.json').read_text())
pairs = {r['id']: r for r in map(json.loads, (HERE / 'pairs.jsonl').open())}


def state(row):
    return row['verdict'] if row['json_valid'] else 'invalid'


def category(row):
    if row['json_valid']:
        return 'valid'
    if row['finish_reason'] == 'length':
        return 'length_limit'
    start = row['raw'].find('{')
    if start < 0:
        return 'missing_json_object'
    try:
        json.JSONDecoder().raw_decode(row['raw'][start:])
    except json.JSONDecodeError:
        return 'json_syntax'
    return 'schema_mismatch'


def positive(row):
    return int(state(row) == 'malicious')


def decomposition(paired):
    valid_pairs = [(a, b) for a, b in paired if a['json_valid'] and b['json_valid']]
    invalid_pairs = [(a, b) for a, b in paired if not (a['json_valid'] and b['json_valid'])]
    total = sum(positive(b) - positive(a) for a, b in paired)
    valid_delta = sum(positive(b) - positive(a) for a, b in valid_pairs)
    invalid_delta = sum(positive(b) - positive(a) for a, b in invalid_pairs)
    assert total == valid_delta + invalid_delta
    return {'n': len(paired), 'both_valid_n': len(valid_pairs),
            'positive_delta': total, 'both_valid_positive_delta': valid_delta,
            'involving_invalid_positive_delta': invalid_delta,
            'transitions': dict(Counter(f'{state(a)}->{state(b)}' for a, b in paired))}


budgets = {}
for budget, folder in [(512, BASE), (2048, HERE)]:
    rows = list(map(json.loads, (folder / 'results.jsonl').open()))
    assert len(rows) == 3892 and not any(r.get('error') for r in rows)
    indexed = {(r['model'], r['config'], r['pair_id']): r for r in rows}
    assert len(indexed) == len(rows)
    budgets[budget] = indexed
assert budgets[512].keys() == budgets[2048].keys()

budget_effects, intent_effects = [], []
for model in protocol['models']:
    for config in protocol['configs']:
        keys = [k for k in budgets[512] if k[:2] == (model['id'], config)]
        limited = [(budgets[512][k], budgets[2048][k]) for k in keys
                   if budgets[512][k]['finish_reason'] == 'length']
        budget_effects.append({
            'model': model['id'], 'config': config,
            'previously_length_limited': len(limited),
            'new_state_of_previously_length_limited': dict(Counter(category(b) for a, b in limited)),
            'subsets': {subset: decomposition([(budgets[512][k], budgets[2048][k])
                                               for k in keys if pairs[k[2]]['subset'] == subset])
                        for subset in ['MAL', 'TYP']}})
    for budget, indexed in budgets.items():
        intent_effects.append({
            'model': model['id'], 'max_tokens': budget,
            'subsets': {subset: decomposition([
                (indexed[model['id'], 'DIFF', pair_id], indexed[model['id'], 'DIFF+I', pair_id])
                for pair_id, pair in pairs.items() if pair['subset'] == subset])
                for subset in ['MAL', 'TYP']}})

result = {'complete': True, 'exploratory': True,
          'interpretation': 'Arithmetic decomposition; selected both-valid subsets are not an unbiased estimate of intent effects.',
          'budget_effects': budget_effects, 'intent_effects': intent_effects}
(HERE / 'diagnostics.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
