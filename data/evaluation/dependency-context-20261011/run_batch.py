"""Run the frozen conditional-version study on the local model server."""
import hashlib
import json
import time
import urllib.request
from pathlib import Path
import jsonschema
from transformers import AutoTokenizer
from prompts import ARMS, IDS_SCHEMA, build, audit

HERE = Path(__file__).resolve().parent


def post(route, payload):
    req = urllib.request.Request('http://127.0.0.1:8101/' + route, data=json.dumps(payload).encode(),
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=300) as response:
        return json.load(response)


def parse(raw, finish):
    if finish == 'length':
        return None
    try:
        obj, _ = json.JSONDecoder().raw_decode(raw[raw.index('{'):])
        jsonschema.validate(obj, IDS_SCHEMA)
        return obj
    except (ValueError, jsonschema.ValidationError):
        return None


def run():
    protocol = json.loads((HERE / 'protocol.json').read_text())
    pairs = [json.loads(line) for line in (HERE / 'pairs.jsonl').open()]
    snapshots = json.loads((HERE / 'context-snapshots.json').read_text())
    model = protocol['model']
    tokenizer = AutoTokenizer.from_pretrained(model['path'], local_files_only=True, trust_remote_code=False)
    output = HERE / 'results.jsonl'
    rows = [json.loads(l) for l in output.open()] if output.exists() else []
    index = {(r['pair_id'], r['arm']): r for r in rows}
    assert len(index) == len(rows) and not any(r.get('transport_error') for r in rows)
    for arm in ARMS:
        pair = max(pairs, key=lambda p: len(build(p, snapshots[arm])[1]['content']))
        messages = build(pair, snapshots[arm])
        local = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True)['input_ids']
        remote = post('tokenize', {'model': model['id'], 'messages': messages, 'add_generation_prompt': True})
        assert local == remote['tokens'] and remote['max_model_len'] == 32768
    for pair in pairs:
        for arm in ARMS:
            if (pair['id'], arm) in index:
                continue
            snapshot = snapshots[arm]
            messages = build(pair, snapshot)
            ids = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True)['input_ids']
            assert len(ids) + 2048 <= 32768
            payload = {'model': model['id'], 'messages': messages, 'temperature': 0, 'top_p': 1,
                       'seed': 0, 'max_tokens': 2048,
                       'response_format': {'type': 'json_schema', 'json_schema': {
                           'name': 'decision', 'strict': True, 'schema': IDS_SCHEMA}}}
            row = {'pair_id': pair['id'], 'arm': arm, 'model': model['id'],
                   'request_sha256': hashlib.sha256(json.dumps(payload).encode()).hexdigest(),
                   'expected_prompt_tokens': len(ids), 'human_annotation_verified': False,
                   'conditional_version': snapshot['version'], 'actual_installed_version_verified': False,
                   'json_valid': False, 'parsed': None}
            start = time.monotonic()
            try:
                response = post('v1/chat/completions', payload)
                choice = response['choices'][0]
                raw = choice['message']['content'] or ''
                parsed = parse(raw, choice['finish_reason'])
                row.update(raw=raw, parsed=parsed, json_valid=parsed is not None,
                           finish_reason=choice['finish_reason'], usage=response['usage'],
                           response_id=response['id'], latency_ms=1000*(time.monotonic()-start))
                if parsed:
                    row['citation_audit'] = audit(pair, snapshot, parsed['evidence_ids'])
            except Exception as error:
                row['transport_error'] = repr(error)
            with output.open('a') as stream:
                stream.write(json.dumps(row, ensure_ascii=False) + '\n')
                stream.flush()
            index[pair['id'], arm] = row
            print(json.dumps({'completed': len(index), 'expected': 40, 'pair_id': pair['id'], 'arm': arm}), flush=True)
            if row.get('transport_error'):
                raise RuntimeError(row['transport_error'])
            assert row['usage']['prompt_tokens'] == len(ids)
