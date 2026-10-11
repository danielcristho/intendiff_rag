"""Run all development arms against the already started local model server."""
import hashlib
import json
import time
import urllib.request
from pathlib import Path

import jsonschema
from transformers import AutoTokenizer

from evidence import audit_ids
from prompts import ARMS, build, schema

HERE = Path(__file__).resolve().parent


def post(route, payload):
    request = urllib.request.Request('http://127.0.0.1:8101/' + route,
                                    data=json.dumps(payload).encode(),
                                    headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(request, timeout=300) as response:
        return json.load(response)


def parse(raw, finish, arm):
    if finish == 'length':
        return None, 'length'
    try:
        value, _ = json.JSONDecoder().raw_decode(raw[raw.index('{'):])
        jsonschema.validate(value, schema(arm))
        return value, None
    except (ValueError, jsonschema.ValidationError) as error:
        return None, type(error).__name__


def run():
    protocol = json.loads((HERE / 'protocol.json').read_text())
    pairs = [json.loads(l) for l in (HERE / 'pairs.jsonl').open()]
    model = protocol['model']
    tokenizer = AutoTokenizer.from_pretrained(model['path'], local_files_only=True, trust_remote_code=False)
    output = HERE / 'results.jsonl'
    rows = [json.loads(l) for l in output.open()] if output.exists() else []
    index = {(r['pair_id'], r['arm']): r for r in rows}
    assert len(index) == len(rows)
    if any(r.get('transport_error') for r in rows):
        raise RuntimeError('Transport error retained; inspect before any retry')
    checks = []
    for arm in ARMS[:-1]:
        pair = max(pairs, key=lambda p: len(build(arm, p)[1]['content']))
        messages = build(arm, pair)
        local = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True)['input_ids']
        remote = post('tokenize', {'model': model['id'], 'messages': messages, 'add_generation_prompt': True})
        assert local == remote['tokens'] and remote['max_model_len'] == 32768
        checks.append({'arm': arm, 'pair_id': pair['id'], 'tokens': len(local), 'match': True})
    (HERE / 'server-check.json').write_text(json.dumps(checks, indent=2) + '\n')
    for pair in pairs:
        for arm in ARMS:
            if (pair['id'], arm) in index:
                continue
            candidate = None
            if arm == 'VERIFY-I':
                prior = index[pair['id'], 'IDS-I']
                candidate = prior['parsed'] or {'invalid_candidate_raw': prior['raw']}
            messages = build(arm, pair, candidate)
            ids = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True)['input_ids']
            if len(ids) + protocol['max_tokens'] > protocol['max_model_len']:
                raise RuntimeError('Actual request exceeds context; no truncation allowed')
            payload = {'model': model['id'], 'messages': messages, 'temperature': 0,
                       'top_p': 1, 'seed': 0, 'max_tokens': protocol['max_tokens']}
            if arm != 'LEGACY-I':
                payload['response_format'] = {'type': 'json_schema', 'json_schema': {
                    'name': 'decision', 'strict': True, 'schema': schema(arm)}}
            record = {'pair_id': pair['id'], 'arm': arm, 'model': model['id'],
                      'request_sha256': hashlib.sha256(json.dumps(payload).encode()).hexdigest(),
                      'expected_prompt_tokens': len(ids), 'human_annotation_verified': False,
                      'json_valid': False, 'parsed': None}
            started = time.monotonic()
            try:
                response = post('v1/chat/completions', payload)
                choice = response['choices'][0]
                raw = choice['message']['content'] or ''
                parsed, error = parse(raw, choice['finish_reason'], arm)
                record.update(raw=raw, finish_reason=choice['finish_reason'], parsed=parsed,
                              parse_error=error, json_valid=parsed is not None,
                              usage=response['usage'], response_id=response['id'],
                              latency_ms=1000 * (time.monotonic() - started))
                if parsed and arm in ['IDS-I', 'IDS-D', 'VERIFY-I']:
                    record['citation_audit'] = audit_ids(pair['diff'], parsed['evidence_ids'])
                if arm == 'VERIFY-I':
                    record['candidate_request_sha256'] = prior['request_sha256']
            except Exception as error:
                record['transport_error'] = repr(error)
            with output.open('a') as stream:
                stream.write(json.dumps(record, ensure_ascii=False) + '\n')
                stream.flush()
            index[pair['id'], arm] = record
            print(json.dumps({'completed': len(index), 'expected': 160, 'pair_id': pair['id'],
                              'arm': arm, 'valid': record['json_valid']}), flush=True)
            if record.get('transport_error'):
                raise RuntimeError(record['transport_error'])
            assert record['usage']['prompt_tokens'] == len(ids)


if __name__ == '__main__':
    run()
