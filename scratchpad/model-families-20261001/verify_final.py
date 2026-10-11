"""Verify completed artifacts and preserve the evidence in verification.json."""
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'data/evaluation/model-families-20261001'
protocol = json.loads((HERE / 'protocol.json').read_text())
summary = json.loads((HERE / 'summary.json').read_text())
comparison = json.loads((HERE / 'comparison.json').read_text())
status = json.loads((HERE / 'status.json').read_text())
assert summary['complete'] and comparison['complete'] and status['stage'] == 'complete'
assert comparison['combined_runs'] == 11676 and len(comparison['groups']) == 12
assert summary['unique_runs'] == summary['attempt_records'] == 3892
checked = {}
initial = json.loads((HERE / 'protocol.initial.json').read_text())
assert protocol['kv_cache_memory_bytes'] == 6 * 2**30
assert protocol['amendments'][0]['new_inferences_before_change'] == 0
for name, expected in initial['source_sha256'].items():
    archived = HERE / 'startup-initial' / Path(name).name
    assert hashlib.sha256(archived.read_bytes()).hexdigest() == expected, name
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
options = {m['id']: m for m in protocol['models']}
assert all(r['stop_token_ids'] == options[r['model']]['stop_token_ids'] for r in rows)
assert all(r['response_model'] == r['model'] for r in rows)
assert all(r.get('stop_reason') is None or r['stop_reason'] in r['stop_token_ids'] for r in rows)
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
    statuses = Counter(re.findall(r'POST /v1/chat/completions HTTP/1\.1" (\d+)', current))
    assert statuses == {'200': 1946}, statuses
    tokenizations = Counter(re.findall(r'POST /tokenize HTTP/1\.1" (\d+)', current))
    assert tokenizations == {'200': 2}, tokenizations
    check = json.loads((HERE / f'{model["tag"]}.server-check.json').read_text())
    assert check['verified'] and all(c['token_ids_match'] for c in check['checks'])
    assert 'Application shutdown complete' in current
    assert 'kv_cache_memory_bytes=6442450944' in current or "'kv_cache_memory_bytes': 6442450944" in current
    logs[model['tag']] = {'http_post_statuses': dict(statuses),
                          'tokenize_statuses': dict(tokenizations),
                          'tokenizer_matches_local_audit': True,
                          'application_shutdown_complete': True}

result = {'verified': True, 'unique_runs': len(rows), 'attempt_records': summary['attempt_records'],
          'expected_groups': 4, 'pairs_per_group': 973, 'frozen_hash_checks': checked,
          'archived_initial_source_hash_checks': len(initial['source_sha256']),
          'native_stop_tokens_and_response_model_checked': True,
          'kv_cache_memory_bytes': protocol['kv_cache_memory_bytes'],
          'amendment_before_first_prediction_verified': True,
          'metrics_independently_recounted': True, 'output_and_context_limits_checked': True,
          'historical_control': True, 'human_annotation_verified': False, 'server_logs': logs}
(HERE / 'verification.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
