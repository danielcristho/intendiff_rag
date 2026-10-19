"""Verify completed D85 outputs against the frozen protocol and raw responses."""
import hashlib
import json
import shutil
import sys
from pathlib import Path

import jsonschema
from transformers import AutoTokenizer

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'data/evaluation/evidence-dev-20261001'
sys.path.insert(0, str(HERE))
from evidence import audit_ids
from prompts import build, schema

protocol = json.loads((HERE / 'protocol.json').read_text())
verified = {}
for section in ['source_sha256', 'upstream_sha256', 'model_sha256']:
    for name, expected_hash in protocol[section].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected_hash, name
    verified[section] = len(protocol[section])
pairs = {p['id']: p for p in map(json.loads, (HERE / 'pairs.jsonl').open())}
rows = [json.loads(l) for l in (HERE / 'results.jsonl').open()]
index = {(r['pair_id'], r['arm']): r for r in rows}
assert len(rows) == len(index) == 160
assert set(index) == {(pid, arm) for pid in pairs for arm in protocol['arms']}
assert not any(r.get('transport_error') for r in rows)
tokenizer = AutoTokenizer.from_pretrained(protocol['model']['path'], local_files_only=True, trust_remote_code=False)
for row in rows:
    pair, arm = pairs[row['pair_id']], row['arm']
    candidate = None
    if arm == 'VERIFY-I':
        prior = index[pair['id'], 'IDS-I']
        candidate = prior['parsed'] or {'invalid_candidate_raw': prior['raw']}
        assert row['candidate_request_sha256'] == prior['request_sha256']
    messages = build(arm, pair, candidate)
    ids = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True)['input_ids']
    assert len(ids) == row['expected_prompt_tokens'] == row['usage']['prompt_tokens']
    assert len(ids) + 2048 <= 32768
    payload = {'model': protocol['model']['id'], 'messages': messages,
               'temperature': 0, 'top_p': 1, 'seed': 0, 'max_tokens': 2048}
    if arm != 'LEGACY-I':
        payload['response_format'] = {'type': 'json_schema', 'json_schema': {
            'name': 'decision', 'strict': True, 'schema': schema(arm)}}
    assert hashlib.sha256(json.dumps(payload).encode()).hexdigest() == row['request_sha256']
    parsed = None
    if row['finish_reason'] != 'length':
        try:
            value, _ = json.JSONDecoder().raw_decode(row['raw'][row['raw'].index('{'):])
            jsonschema.validate(value, schema(arm))
            parsed = value
        except (ValueError, jsonschema.ValidationError):
            pass
    assert (parsed is not None) == row['json_valid']
    assert parsed == row['parsed']
    if parsed and arm in ['IDS-I', 'IDS-D', 'VERIFY-I']:
        assert audit_ids(pair['diff'], parsed['evidence_ids']) == row['citation_audit']
    assert row['human_annotation_verified'] is False
log = (HERE / 'server.log').read_text()
generations = log.count('POST /v1/chat/completions HTTP/1.1" 200 OK')
tokenizations = log.count('POST /tokenize HTTP/1.1" 200 OK')
assert generations == 160 and tokenizations == 4, (generations, tokenizations)
assert 'Shutting down' in log or 'shutdown' in log
status = json.loads((HERE / 'status.json').read_text())
assert status['stage'] == 'complete'
path = HERE / 'verification.json'
previous = json.loads(path.read_text())
if not previous.get('completed_inference') and not (HERE / 'verification.pre-run.json').exists():
    shutil.copyfile(path, HERE / 'verification.pre-run.json')
report = {'completed_inference': True, 'actual_generations': len(rows),
          'pairs': len(pairs), 'arms': protocol['arms'], 'verified_hash_counts': verified,
          'all_request_hashes_match': True, 'all_actual_prompt_tokens_match': True,
          'raw_response_parsing_matches': True, 'citation_audits_match': True,
          'generation_http_200': generations, 'tokenization_http_200': tokenizations,
          'human_annotation_verified': False, 'accuracy_metrics_available': False,
          'prior_cuda_failure_preserved': 'Segfault encountered' in log,
          'post_restart_probe': 'scratchpad/cuda-recovery-20261001/resume-probe-20261001T143835Z.json'}
path.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
