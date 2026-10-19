"""Reconstruct D88 requests, citations, metrics and frozen provenance."""
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

import jsonschema
from transformers import AutoTokenizer

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'data/evaluation/dependency-context-20261011'
sys.path.insert(0, str(HERE))
from evaluate import verify
from prompts import ARMS, IDS_SCHEMA, build, audit


def read(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


protocol = json.loads((HERE / 'protocol.json').read_text())
verify(protocol)
pairs = {p['id']: p for p in read(HERE / 'pairs.jsonl')}
historical_pairs = {p['id']: p for p in read(HERE.parent / 'mixed-validation-20261011/pairs.jsonl')}
snapshots = json.loads((HERE / 'context-snapshots.json').read_text())
provenance = json.loads((HERE / 'dependency-audit.json').read_text())
for version in provenance['dependency_versions']:
    for name, record in version['files'].items():
        raw = Path(record['path']).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == record['sha256']
        assert snapshots['CTX-' + version['version']]['files'][name] == raw.decode()
    assert hashlib.sha256((ROOT / version['metadata_path']).read_bytes()).hexdigest() == version['metadata_sha256']
    assert hashlib.sha256(Path(version['archive']).read_bytes()).hexdigest() == version['archive_sha256']
for pair in pairs.values():
    assert pair == historical_pairs[pair['id']]
    assert hashlib.sha256(pair['diff'].encode()).hexdigest() == pair['diff_sha256']
rows = read(HERE / 'results.jsonl')
index = {(r['pair_id'], r['arm']): r for r in rows}
assert len(index) == len(rows) == 40
assert set(index) == {(p, a) for p in pairs for a in ARMS}
assert len({r['response_id'] for r in rows}) == 40
tokenizer = AutoTokenizer.from_pretrained(protocol['model']['path'], local_files_only=True, trust_remote_code=False)
for row in rows:
    pair, snapshot = pairs[row['pair_id']], snapshots[row['arm']]
    messages = build(pair, snapshot)
    payload = {'model': protocol['model']['id'], 'messages': messages, 'temperature': 0,
               'top_p': 1, 'seed': 0, 'max_tokens': 2048,
               'response_format': {'type': 'json_schema', 'json_schema': {
                   'name': 'decision', 'strict': True, 'schema': IDS_SCHEMA}}}
    assert hashlib.sha256(json.dumps(payload).encode()).hexdigest() == row['request_sha256']
    ids = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True)['input_ids']
    assert len(ids) == row['expected_prompt_tokens'] == row['usage']['prompt_tokens']
    assert len(ids) + 2048 <= 32768 and 0 < row['usage']['completion_tokens'] <= 2048
    parsed = None
    if row['finish_reason'] != 'length':
        try:
            obj, _ = json.JSONDecoder().raw_decode(row['raw'][row['raw'].index('{'):])
            jsonschema.validate(obj, IDS_SCHEMA)
            parsed = obj
        except (ValueError, jsonschema.ValidationError):
            pass
    assert (parsed is not None) == row['json_valid'] and parsed == row['parsed']
    if parsed:
        assert audit(pair, snapshot, parsed['evidence_ids']) == row['citation_audit']
    assert row['human_annotation_verified'] is False and not row.get('transport_error')
    assert row['actual_installed_version_verified'] is False
    assert row['conditional_version'] == snapshot['version']
summary = json.loads((HERE / 'summary.json').read_text())
for group in summary['groups']:
    selected = [r for r in rows if r['arm'] == group['arm']]
    counts = Counter(r['parsed']['verdict'] if r['json_valid'] else 'invalid' for r in selected)
    assert group['n'] == len(selected) == 20 and group['verdicts'] == counts
    assert group['valid'] == sum(r['json_valid'] for r in selected)
    for field in ('prompt_tokens', 'completion_tokens'):
        assert group[field] == sum(r['usage'][field] for r in selected)
historical = [r for r in read(HERE.parent / 'mixed-validation-20261011/results.jsonl')
              if r['pair_id'] in pairs and r['arm'] == 'IDS-I']
assert len(historical) == 20
assert all(r['json_valid'] and r['parsed']['verdict'] == 'benign' for r in historical)
log = (HERE / 'server.log').read_text()
statuses = Counter(re.findall(r'POST /v1/chat/completions HTTP/1\.1" (\d+)', log))
assert statuses == {'200': 40}, statuses
assert log.count('POST /tokenize HTTP/1.1" 200 OK') == 2
assert 'Application shutdown complete' in log
assert json.loads((HERE / 'status.json').read_text())['stage'] == 'complete'
result = {'verified': True, 'new_generations': 40, 'historical_IDS_I_controls': 20,
          'request_hashes_prompt_tokens_parsing_citations_match': True,
          'source_archive_metadata_and_context_bytes_match': True,
          'pairs_match_D87_exactly': True, 'metrics_recounted': True,
          'http_generation_statuses': dict(statuses), 'server_shutdown_complete': True,
          'frozen_hash_counts': {k: len(protocol[k]) for k in ('source_sha256', 'upstream_sha256', 'model_sha256')},
          'human_annotation_verified': False, 'installed_versions_verified': False,
          'FPR_available': False, 'RAG_evaluated': False}
(HERE / 'verification.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
