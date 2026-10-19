"""Verify paired records and compare two new families with four historical models."""
import hashlib
import json
from collections import Counter
from pathlib import Path

from prompts import build
from compare_report import write_report

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
protocol = json.loads((HERE / 'protocol.json').read_text())
BASE = ROOT / protocol['baseline_directory']
historical = json.loads((BASE / 'comparison.json').read_text())
summary = json.loads((HERE / 'summary.json').read_text())
assert historical['complete'] and historical['combined_runs'] == 7784
assert summary['complete'] and summary['unique_runs'] == 3892
old = list(map(json.loads, (BASE / 'results.all-models.jsonl').open()))
new = list(map(json.loads, (HERE / 'results.jsonl').open()))
rows = old + new
assert len(old) == 7784 and len(new) == 3892
assert len(rows) == len({r['run_key'] for r in rows}) == 11676
assert not any(r.get('error') for r in rows)
pairs = {p['id']: p for p in map(json.loads, (HERE / 'pairs.jsonl').open())}
audited = {(r['model'], r['config'], r['pair_id']): r
           for r in map(json.loads, (HERE / 'context-audit.jsonl').open())}
options = {m['id']: m for m in protocol['models']}
for row in new:
    expected = audited[row['model'], row['config'], row['pair_id']]
    assert row['max_tokens'] == 2048 and row['experiment_id'] == protocol['experiment_id']
    assert row['prompt_tokens'] == expected['prompt_tokens']
    assert row['prompt_messages_sha256'] == expected['prompt_messages_sha256']
    assert row['chat_template_kwargs'] == expected['chat_template_kwargs']
    assert row['stop_token_ids'] == options[row['model']]['stop_token_ids']
    assert row['response_model'] == row['model']
    assert 0 < row['completion_tokens'] <= 2048 and row['prompt_tokens'] + 2048 <= 32768
groups = historical['groups'] + summary['groups']
indexed = {(r['model'], r['config'], r['pair_id']): r for r in rows}
for group in groups:
    selected = [r for r in rows if (r['model'], r['config']) == (group['model'], group['config'])]
    assert len(selected) == 973 and {r['pair_id'] for r in selected} == pairs.keys()
    assert sum(r['json_valid'] for r in selected) == group['json_valid']
    for subset, metric in [('MAL', 'mal_source_recall_proxy'), ('TYP', 'typ_assumed_benign_fpr')]:
        selected_subset = [r for r in selected if pairs[r['pair_id']]['subset'] == subset]
        assert group[metric]['n'] == len(selected_subset)
        assert group[metric]['positive'] == sum(r['json_valid'] and r['verdict'] == 'malicious'
                                               for r in selected_subset)


def state(row):
    return row['verdict'] if row['json_valid'] else 'invalid'


comparisons = []
for model in protocol['models']:
    for reference in model['comparison_models']:
        for config in protocol['configs']:
            paired = [(indexed[reference, config, pid], indexed[model['id'], config, pid]) for pid in pairs]
            for a, b in paired:
                for field in ['config', 'pair_id', 'seed', 'temperature', 'top_p', 'top_k', 'max_tokens',
                    'label', 'truncated', 'cards', 'diff_sha256', 'evaluation_scope',
                    'label_origin', 'human_annotation_verified']:
                    assert a[field] == b[field], (field, b['pair_id'])
                messages = build(config, pairs[b['pair_id']])
                assert hashlib.sha256(json.dumps(messages).encode()).hexdigest() == b['prompt_messages_sha256']
            subsets = {}
            for subset in ['MAL', 'TYP']:
                selected = [(a, b) for a, b in paired if pairs[a['pair_id']]['subset'] == subset]
                both_valid_net = invalid_net = 0
                for a, b in selected:
                    delta = int(state(b) == 'malicious') - int(state(a) == 'malicious')
                    if a['json_valid'] and b['json_valid']:
                        both_valid_net += delta
                    else:
                        invalid_net += delta
                subsets[subset] = {'n': len(selected),
                    'transitions': dict(Counter(f'{state(a)}->{state(b)}' for a, b in selected)),
                    'net_positive_change': both_valid_net + invalid_net,
                    'both_valid_net_positive_change': both_valid_net,
                    'any_invalid_net_positive_change': invalid_net,
                    'delta_percentage_points': 100 * (both_valid_net + invalid_net) / len(selected)}
            comparisons.append({'reference_model': reference, 'new_model': model['id'],
                                'size_group': model['size_group'], 'config': config, 'subsets': subsets})
result = {'complete': True, 'experiment_id': protocol['experiment_id'], 'new_runs': 3892,
          'historical_runs': 7784, 'combined_runs': 11676, 'historical_control': True,
          'human_annotation_verified': False, 'groups': groups, 'comparisons': comparisons}
(HERE / 'comparison.json').write_text(json.dumps(result, indent=2) + '\n')
(HERE / 'results.all-models.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows))
write_report(result, HERE)
print(json.dumps({'complete': True, 'new_runs': 3892, 'combined_runs': 11676}), flush=True)
