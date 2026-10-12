"""Independently reconstruct every saved request and require complete coverage."""
import json
import re

import jsonschema
from transformers import AutoTokenizer

from common import ARMS, HERE, ROOT, digest, payload, read_rows, request_hash, token_ids, write_json
from evidence import audit_ids
from prompts import schema


def verify_pins(protocol, model=None):
    for path, expected in protocol['source_sha256'].items():
        assert digest(ROOT / path) == expected, path
    if model is not None:
        for row in json.loads((HERE / f"{model['tag']}.model-manifest.json").read_text()):
            assert digest(ROOT / row['path']) == row['sha256'], row['path']


def verify_model(model):
    pairs = {p['id']: p for p in read_rows(HERE / 'pairs.jsonl')}
    rows = read_rows(HERE / f"{model['tag']}.results.jsonl")
    index = {(r['pair_id'], r['arm']): r for r in rows}
    assert len(rows) == len(index) == len(pairs) * len(ARMS) == 2919
    assert set(index) == {(p, a) for p in pairs for a in ARMS}
    assert [(r['pair_id'], r['arm']) for r in rows] == [(p, a) for p in pairs for a in ARMS]
    assert len({r['response_id'] for r in rows}) == len(rows)
    tokenizer = AutoTokenizer.from_pretrained(model['path'], local_files_only=True, trust_remote_code=False)
    for row in rows:
        pair, arm = pairs[row['pair_id']], row['arm']
        candidate = None
        if arm == 'VERIFY-I':
            prior = index[row['pair_id'], 'IDS-I']
            candidate = prior['parsed'] if prior['parsed'] is not None else {'invalid_candidate_raw': prior['raw']}
            assert row['candidate_request_sha256'] == prior['request_sha256']
        body = payload(model, arm, pair, candidate)
        assert row['request_sha256'] == request_hash(body)
        count = len(token_ids(tokenizer, model, body['messages']))
        assert row['usage']['prompt_tokens'] == row['expected_prompt_tokens'] == count
        assert count + 2048 <= 32768 and 0 < row['usage']['completion_tokens'] <= 2048
        parsed = None
        if row['finish_reason'] != 'length':
            try:
                parsed, _ = json.JSONDecoder().raw_decode(row['raw'][row['raw'].index('{'):])
                jsonschema.validate(parsed, schema(arm))
            except (ValueError, jsonschema.ValidationError):
                parsed = None
        assert row['parsed'] == parsed and row['json_valid'] == (parsed is not None)
        if parsed is not None:
            assert audit_ids(pair['diff'], parsed['evidence_ids']) == row['citation_audit']
        assert row['model'] == model['id'] and not row.get('transport_error')
        assert row['experiment_id'] == HERE.name and row['human_annotation_verified'] is False
        assert row['label'] == pair['label'] and row['label_origin'] == pair['label_origin']
        assert row['diff_sha256'] == pair['diff_sha256']
    log = (HERE / f"{model['tag']}.server.log").read_text()
    codes = re.findall(r'POST /v1/chat/completions HTTP/1\.1" (\d+)', log)
    assert len(codes) == 2919 and set(codes) == {'200'}
    assert 'Application shutdown complete' in log
    write_json(HERE / f"{model['tag']}.verification.json", {
        'verified': True, 'new_generations': len(rows), 'pairs': len(pairs),
        'complete_matrix': True, 'payload_tokens_parser_citations_reconstructed': True,
        'http_200_generations': len(codes), 'human_gold_verified': False})
