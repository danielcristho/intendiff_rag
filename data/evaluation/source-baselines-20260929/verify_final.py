"""Run after evaluate.py finishes: python verify_final.py."""
import csv
import json
import math
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
protocol = json.loads((HERE / 'protocol.json').read_text())
summary = json.loads((HERE / 'summary.json').read_text())
status = json.loads((HERE / 'status.json').read_text())
assert status['stage'] == 'complete' and summary['complete']
pairs = {row['id']: row for row in map(json.loads, (HERE / 'pairs.jsonl').open())}
rows = list(map(json.loads, (HERE / 'results.jsonl').open()))
assert len(rows) == protocol['expected_runs'] == 3892
expected = {(model['id'], config, pair) for model in protocol['models']
            for config in protocol['configs'] for pair in pairs}
assert {(r['model'], r['config'], r['pair_id']) for r in rows} == expected
assert len({r['run_key'] for r in rows}) == len(rows)
for row in rows:
    assert not row.get('error') and row['cards'] == []
    assert row['seed'] == 0 and row['temperature'] == 0 and row['top_p'] == 1
    assert row['evaluation_scope'] == 'exploratory_source_labels'
    assert row['human_annotation_verified'] is False
    assert row['completion_tokens'] <= protocol['max_tokens']
    assert row['prompt_tokens'] + row['completion_tokens'] <= protocol['max_model_len']
    assert row['latency_ms'] > 0
    assert row['label'] == pairs[row['pair_id']]['label']

with (HERE / 'summary.csv').open() as stream:
    csv_groups = {(r['model'], r['config']): r for r in csv.DictReader(stream)}
checks = []
for group in summary['groups']:
    selected = [r for r in rows if (r['model'], r['config']) == (group['model'], group['config'])]
    assert len(selected) == group['completed'] == 973
    assert group['transport_errors'] == 0
    assert group['json_valid'] == sum(r['json_valid'] for r in selected)
    assert Counter(pairs[r['pair_id']]['subset'] for r in selected) == {'MAL': 873, 'TYP': 100}
    csv_group = csv_groups[group['model'], group['config']]
    assert int(csv_group['completed']) == 973 and csv_group['complete_summary'] == 'True'
    for subset, metric in [('MAL', 'mal_source_recall_proxy'), ('TYP', 'typ_assumed_benign_fpr')]:
        subset_rows = [r for r in selected if pairs[r['pair_id']]['subset'] == subset]
        positive = sum(r['json_valid'] and r['verdict'] == 'malicious' for r in subset_rows)
        assert group[metric]['positive'] == positive and group[metric]['n'] == len(subset_rows)
        assert math.isclose(float(csv_group[metric]), positive / len(subset_rows))
    latency = sorted(r['latency_ms'] for r in selected)
    for key, fraction in [('median_latency_ms', .5), ('p95_latency_ms', .95)]:
        assert group['cost'][key] == latency[math.ceil(fraction * len(latency)) - 1]
    checks.append({'model': group['model'], 'config': group['config'], 'verified_runs': len(selected)})

server_requests = {}
for model in protocol['models']:
    log = (HERE / f"{model['tag']}.server.log").read_text()
    count = sum('POST /v1/chat/completions ' in line and '200 OK' in line for line in log.splitlines())
    raw = list(map(json.loads, (HERE / f"{model['tag']}.results.jsonl").open()))
    newest = {r['run_key']: r for r in raw}
    assert len(newest) == 1946 and count >= 1946
    assert all(newest[r['run_key']] == r for r in rows if r['model'] == model['id'])
    server_requests[model['id']] = {'http_200': count, 'recorded_attempts': len(raw)}

result = {'verified': True, 'unique_runs': len(rows), 'groups': checks,
          'server_requests': server_requests, 'human_annotation_verified': False}
(HERE / 'verification.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
