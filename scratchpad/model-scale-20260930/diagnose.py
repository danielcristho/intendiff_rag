"""Partition paired detection changes into valid verdicts and invalid transitions."""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'data/evaluation/model-scale-20260930'
comparison = json.loads((HERE / 'comparison.json').read_text())
assert comparison['complete']
rows = list(map(json.loads, (HERE / 'results.all-models.jsonl').open()))
indexed = {(r['model'], r['config'], r['pair_id']): r for r in rows}
pairs = list(map(json.loads, (HERE / 'pairs.jsonl').open()))
contrasts = [(c['smaller_model'], c['config'], c['larger_model'], c['config'])
             for c in comparison['comparisons']]
models = json.loads((HERE / 'models.json').read_text())
contrasts.extend((m['id'], 'DIFF', m['id'], 'DIFF+I') for m in models)
diagnostics = []
for old_model, old_config, new_model, new_config in contrasts:
    entry = {'before': {'model': old_model, 'config': old_config},
             'after': {'model': new_model, 'config': new_config}, 'subsets': {}}
    for subset in ['MAL', 'TYP']:
        count = net = both_valid_net = invalid_net = both_valid_n = 0
        for pair in pairs:
            if pair['subset'] != subset:
                continue
            old = indexed[old_model, old_config, pair['id']]
            new = indexed[new_model, new_config, pair['id']]
            before = int(old['json_valid'] and old['verdict'] == 'malicious')
            after = int(new['json_valid'] and new['verdict'] == 'malicious')
            change = after - before
            count += 1
            net += change
            if old['json_valid'] and new['json_valid']:
                both_valid_n += 1
                both_valid_net += change
            else:
                invalid_net += change
        assert net == both_valid_net + invalid_net
        entry['subsets'][subset] = {'n': count, 'net_positive_change': net,
                                   'both_valid_n': both_valid_n,
                                   'both_valid_net_positive_change': both_valid_net,
                                   'any_invalid_net_positive_change': invalid_net,
                                   'delta_percentage_points': 100 * net / count}
    diagnostics.append(entry)
result = {'complete': True, 'invalid_policy': 'benign', 'contrasts': diagnostics,
          'interpretation': 'Descriptive partition; not a causal effect of reasoning or size.'}
result['new_output_audit'] = []
for model in models:
    for config in ['DIFF', 'DIFF+I']:
        selected = [r for r in rows if (r['model'], r['config']) == (model['id'], config)]
        errors = Counter()
        for row in selected:
            if row['json_valid'] or row['finish_reason'] == 'length':
                continue
            start = row['raw'].find('{')
            if start < 0:
                errors['missing_json_object'] += 1
                continue
            try:
                json.JSONDecoder().raw_decode(row['raw'][start:])
            except json.JSONDecodeError as error:
                errors[error.msg] += 1
        result['new_output_audit'].append({'model': model['id'], 'config': config,
            'non_length_json_decoder_errors': dict(errors),
            'responses_containing_think_open_tag': sum('<think>' in r['raw'] for r in selected)})
(HERE / 'diagnostics.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
