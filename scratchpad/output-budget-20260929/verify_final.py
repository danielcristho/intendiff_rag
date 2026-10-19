"""Verify completed artifacts and preserve the evidence in verification.json."""
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'data/evaluation/output-budget-20260929'
BASE = ROOT / 'data/evaluation/source-baselines-20260929'
protocol = json.loads((HERE / 'protocol.json').read_text())
summary = json.loads((HERE / 'summary.json').read_text())
comparison = json.loads((HERE / 'comparison.json').read_text())
status = json.loads((HERE / 'status.json').read_text())
assert summary['complete'] and comparison['complete'] and status['stage'] == 'complete'
assert summary['unique_runs'] == summary['attempt_records'] == 3892
checked = {}
for field in ['source_sha256', 'baseline_sha256']:
    for name, expected in protocol[field].items():
        actual = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
        assert actual == expected, name
    checked[field] = len(protocol[field])

rows = list(map(json.loads, (HERE / 'results.jsonl').open()))
assert len(rows) == len({r['run_key'] for r in rows}) == 3892
assert all(not r.get('error') and r['max_tokens'] == 2048
           and r['human_annotation_verified'] is False for r in rows)
assert all(0 < r['completion_tokens'] <= 2048
           and r['prompt_tokens'] + 2048 <= 32768 for r in rows)
pairs = {r['id']: r for r in map(json.loads, (HERE / 'pairs.jsonl').open())}
for group in summary['groups']:
    selected = [r for r in rows if (r['model'], r['config']) == (group['model'], group['config'])]
    assert len(selected) == 973 and {r['pair_id'] for r in selected} == pairs.keys()
    assert sum(r['json_valid'] for r in selected) == group['json_valid']
    for subset, metric in [('MAL', 'mal_source_recall_proxy'), ('TYP', 'typ_assumed_benign_fpr')]:
        subset_rows = [r for r in selected if pairs[r['pair_id']]['subset'] == subset]
        positives = sum(r['json_valid'] and r['verdict'] == 'malicious' for r in subset_rows)
        assert positives == group[metric]['positive'] and len(subset_rows) == group[metric]['n']
        assert positives / len(subset_rows) == group[metric]['rate']

logs = {}
for model in protocol['models']:
    current = (HERE / f'{model["tag"]}.server.log').read_text()
    baseline = (BASE / f'{model["tag"]}.server.log').read_text()
    statuses = Counter(re.findall(r'POST /v1/chat/completions HTTP/1\.1" (\d+)', current))
    assert statuses == {'200': 1946}, statuses
    marker = 'Initializing a V1 LLM engine '
    a = [line.split(marker, 1)[1] for line in baseline.splitlines() if marker in line]
    b = [line.split(marker, 1)[1] for line in current.splitlines() if marker in line]
    assert a and b and a[-1] == b[-1], model['id']
    assert 'Application shutdown complete' in current
    logs[model['tag']] = {'http_post_statuses': dict(statuses),
                          'last_engine_configuration_matches_baseline': True,
                          'application_shutdown_complete': True}

result = {'verified': True, 'unique_runs': len(rows), 'attempt_records': summary['attempt_records'],
          'expected_groups': 4, 'pairs_per_group': 973, 'frozen_hash_checks': checked,
          'metrics_independently_recounted': True, 'output_and_context_limits_checked': True,
          'historical_control': True, 'human_annotation_verified': False, 'server_logs': logs}
(HERE / 'verification.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
