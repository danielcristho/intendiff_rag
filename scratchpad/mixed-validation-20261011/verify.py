"""Reconstruct and verify D87 requests, source labels, metrics and frozen hashes."""
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

import jsonschema
from transformers import AutoTokenizer

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'data/evaluation/mixed-validation-20261011'
sys.path.insert(0, str(HERE))
from evaluate import verify
from prompts import build, schema
from evidence import audit_ids

protocol = json.loads((HERE / 'protocol.json').read_text())
verify(protocol)
read = lambda path: [json.loads(l) for l in path.open()]
pairs = {p['id']: p for p in read(HERE / 'pairs.jsonl')}
source = {p['id']: p for p in read(ROOT / 'data/evaluation/model-families-20261001/pairs.jsonl')}
for pair in pairs.values():
    assert source[pair['id']]['label'] == 'malicious'
    assert pair['diff_sha256'] == source[pair['id']]['diff_sha256']
    assert pair['intent'] == source[pair['id']]['intent']
    assert hashlib.sha256(pair['diff'].encode()).hexdigest() == pair['diff_sha256']
assert len({p['campaign'] for p in pairs.values()}) == 32
rows = read(HERE / 'results.jsonl')
index = {(r['pair_id'], r['arm']): r for r in rows}
assert len(rows) == len(index) == 160
assert set(index) == {(p, a) for p in pairs for a in protocol['arms']}
tokenizer = AutoTokenizer.from_pretrained(protocol['model']['path'], local_files_only=True, trust_remote_code=False)
for r in rows:
    pair, arm = pairs[r['pair_id']], r['arm']
    candidate = None
    if arm == 'VERIFY-I':
        prior = index[pair['id'], 'IDS-I']
        candidate = prior['parsed'] or {'invalid_candidate_raw': prior['raw']}
        assert r['candidate_request_sha256'] == prior['request_sha256']
    messages = build(arm, pair, candidate)
    payload = {'model': protocol['model']['id'], 'messages': messages,
               'temperature': 0, 'top_p': 1, 'seed': 0, 'max_tokens': 2048}
    if arm != 'LEGACY-I':
        payload['response_format'] = {'type': 'json_schema', 'json_schema': {
            'name': 'decision', 'strict': True, 'schema': schema(arm)}}
    assert hashlib.sha256(json.dumps(payload).encode()).hexdigest() == r['request_sha256']
    ids = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True)['input_ids']
    assert len(ids) == r['expected_prompt_tokens'] == r['usage']['prompt_tokens']
    assert len(ids) + 2048 <= 32768 and 0 < r['usage']['completion_tokens'] <= 2048
    parsed = None
    if r['finish_reason'] != 'length':
        try:
            obj, _ = json.JSONDecoder().raw_decode(r['raw'][r['raw'].index('{'):])
            jsonschema.validate(obj, schema(arm))
            parsed = obj
        except (ValueError, jsonschema.ValidationError):
            pass
    assert (parsed is not None) == r['json_valid'] and parsed == r['parsed']
    if parsed and arm in ('IDS-I', 'IDS-D', 'VERIFY-I'):
        assert audit_ids(pair['diff'], parsed['evidence_ids']) == r['citation_audit']
    assert r['human_annotation_verified'] is False and not r.get('transport_error')
hn = read(HERE / 'hn-historical-results.jsonl')
summary = json.loads((HERE / 'summary.json').read_text())
for g in summary['groups']:
    selected = [r for r in (rows if g['cohort'] == 'MAL' else hn) if r['arm'] == g['arm']]
    positives = sum(r['json_valid'] and r['parsed']['verdict'] == 'malicious' for r in selected)
    assert g['n'] == len(selected) == 32 and g['positive'] == positives
    assert g['valid'] == sum(r['json_valid'] for r in selected)
    if g['cohort'] == 'MAL':
        assert g['source_recall_proxy'] == positives / 32
    else:
        assert g['fpr'] is None
log = (HERE / 'server.log').read_text()
statuses = Counter(re.findall(r'POST /v1/chat/completions HTTP/1\.1" (\d+)', log))
assert statuses == {'200': 160}, statuses
assert log.count('POST /tokenize HTTP/1.1" 200 OK') == 4
assert 'Application shutdown complete' in log
assert json.loads((HERE / 'status.json').read_text())['stage'] == 'complete'
result = {'verified': True, 'new_generations': 160, 'historical_hn_generations': 160,
          'all_request_hashes_and_prompt_tokens_match': True, 'raw_parsing_and_citations_match': True,
          'source_MAL_labels_and_inputs_match_historical_corpus': True, 'unique_MAL_campaigns': 32,
          'metrics_recounted': True, 'http_generation_statuses': dict(statuses),
          'server_shutdown_complete': True,
          'frozen_hash_counts': {k: len(protocol[k]) for k in ('source_sha256', 'upstream_sha256', 'model_sha256')},
          'human_annotation_verified': False, 'FPR_available': False}
(HERE / 'verification.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
