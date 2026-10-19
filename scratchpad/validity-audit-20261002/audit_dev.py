"""Reconstruct every D85 request without changing its frozen outputs."""
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

import jsonschema
from transformers import AutoTokenizer

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
HERE = ROOT / 'data/evaluation/evidence-dev-20261001'
sys.path.insert(0, str(HERE))
from evidence import audit_ids
from prompts import build, schema


def digest(path):
    hasher = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(8 * 1024**2), b''):
            hasher.update(chunk)
    return hasher.hexdigest()


protocol = json.loads((HERE / 'protocol.json').read_text())
checked = []
for section in ('source_sha256', 'upstream_sha256', 'model_sha256'):
    for name, expected in protocol[section].items():
        path = ROOT / name
        if name == 'docs/decisions.md':
            path = ROOT / 'data/evaluation/mixed-dev-20261002/decisions-through-D85.md'
        assert digest(path) == expected, str(path)
        checked.append({'section': section, 'pinned': name, 'verified_path': str(path.relative_to(ROOT))})
pairs = {p['id']: p for p in map(json.loads, (HERE / 'pairs.jsonl').open())}
rows = list(map(json.loads, (HERE / 'results.jsonl').open()))
index = {(r['pair_id'], r['arm']): r for r in rows}
assert len(rows) == len(index) == 160
assert set(index) == {(pid, arm) for pid in pairs for arm in protocol['arms']}
tokenizer = AutoTokenizer.from_pretrained(protocol['model']['path'], local_files_only=True, trust_remote_code=False)
counts = {a: Counter() for a in protocol['arms']}
for row in rows:
    pair, arm = pairs[row['pair_id']], row['arm']
    prior = index[pair['id'], 'IDS-I']
    candidate = prior['parsed'] or {'invalid_candidate_raw': prior['raw']} if arm == 'VERIFY-I' else None
    if arm == 'VERIFY-I':
        assert row['candidate_request_sha256'] == prior['request_sha256']
    messages = build(arm, pair, candidate)
    tokens = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True)['input_ids']
    assert len(tokens) == row['expected_prompt_tokens'] == row['usage']['prompt_tokens']
    assert len(tokens) + 2048 <= 32768
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
    assert (parsed is not None) == row['json_valid'] and parsed == row['parsed']
    assert not row.get('transport_error') and row['human_annotation_verified'] is False
    counts[arm]['n'] += 1
    counts[arm]['valid'] += int(parsed is not None)
    counts[arm]['malicious'] += int(parsed is not None and parsed['verdict'] == 'malicious')
    if parsed and arm in ('IDS-I', 'IDS-D', 'VERIFY-I'):
        audit = audit_ids(pair['diff'], parsed['evidence_ids'])
        assert audit == row['citation_audit']
        counts[arm]['header_or_hunk_citations'] += int(any(r['kind'] in ('metadata', 'hunk') for r in audit['referenced_lines']))
        counts[arm]['no_content_citations'] += int(audit['content_line_count'] == 0)
log = (HERE / 'server.log').read_text()
assert log.count('POST /v1/chat/completions HTTP/1.1" 200 OK') == 160
summary = json.loads((HERE / 'summary.json').read_text())
for arm in summary['arms']:
    assert counts[arm['arm']]['valid'] == arm['valid']
    assert counts[arm['arm']]['malicious'] == arm['malicious_predictions']
report = {'passed': True, 'generations': 160, 'reconstructed_requests': 160,
          'retokenized_prompts': 160, 'raw_parsing_and_citations_match': True,
          'frozen_hash_checks': checked, 'arms': counts, 'human_gold_verified': False,
          'accuracy_claim_supported': False, 'source_results_unchanged': True}
(OUT / 'dev-audit.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({k: v for k, v in report.items() if k != 'frozen_hash_checks'}, indent=2))
