"""Run every pair and updated arm once, retaining invalid replies and failures."""
import json
import os
import time
import urllib.request

import jsonschema
from transformers import AutoTokenizer

from common import ARMS, HERE, payload, read_rows, request_hash, token_ids, validate_rows, write_json
from evidence import audit_ids
from prompts import schema


def post(route, body):
    request = urllib.request.Request('http://127.0.0.1:8101/' + route,
        data=json.dumps(body).encode(), headers={'Content-Type': 'application/json'})
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


def candidate_for(prior):
    return prior['parsed'] if prior['parsed'] is not None else {'invalid_candidate_raw': prior['raw']}


def run(model):
    pairs = read_rows(HERE / 'pairs.jsonl')
    result_path = HERE / f"{model['tag']}.results.jsonl"
    rows = read_rows(result_path)
    validate_rows(rows, model, pairs)
    index = {(r['pair_id'], r['arm']): r for r in rows}
    tokenizer = AutoTokenizer.from_pretrained(model['path'], local_files_only=True, trust_remote_code=False)
    audited = {(r['pair_id'], r['arm']): r['prompt_tokens'] for r in
               read_rows(HERE / 'token-audit.jsonl') if r['model_tag'] == model['tag']}
    checks = []
    for arm in ARMS[:2]:
        pair = max(pairs, key=lambda p: audited[p['id'], arm])
        messages = payload(model, arm, pair)['messages']
        ids = token_ids(tokenizer, model, messages)
        remote = post('tokenize', {'model': model['id'], 'messages': messages,
            'add_generation_prompt': True, 'chat_template_kwargs': model['chat_template_kwargs']})
        assert remote['tokens'] == ids and remote['max_model_len'] == 32768
        checks.append({'arm': arm, 'pair_id': pair['id'], 'token_ids_match': True, 'tokens': len(ids)})
    write_json(HERE / f"{model['tag']}.server-check.json", checks)
    for pair in pairs:
        for arm in ARMS:
            if (pair['id'], arm) in index:
                continue
            prior = index.get((pair['id'], 'IDS-I'))
            candidate = candidate_for(prior) if arm == 'VERIFY-I' else None
            body = payload(model, arm, pair, candidate)
            ids = token_ids(tokenizer, model, body['messages'])
            assert len(ids) + 2048 <= 32768, 'Actual verifier exceeds frozen context; no silent truncation'
            if arm != 'VERIFY-I':
                assert len(ids) == audited[pair['id'], arm]
            record = {'experiment_id': HERE.name, 'model': model['id'], 'pair_id': pair['id'],
                'arm': arm, 'seed': 0, 'label': pair['label'], 'label_origin': pair['label_origin'],
                'subset': pair['subset'], 'campaign': pair.get('campaign'),
                'human_annotation_verified': False, 'request_sha256': request_hash(body),
                'diff_sha256': pair['diff_sha256'], 'expected_prompt_tokens': len(ids),
                'json_valid': False, 'parsed': None, 'max_tokens': 2048,
                'additional_truncation': pair['full_method_additional_truncation']}
            if arm == 'VERIFY-I':
                record['candidate_request_sha256'] = prior['request_sha256']
            started = time.monotonic()
            try:
                response = post('v1/chat/completions', body)
                choice = response['choices'][0]
                raw = choice['message']['content'] or ''
                parsed, error = parse(raw, choice['finish_reason'], arm)
                record.update(raw=raw, finish_reason=choice['finish_reason'], parsed=parsed,
                    parse_error=error, json_valid=parsed is not None, usage=response['usage'],
                    response_id=response['id'], latency_ms=1000 * (time.monotonic() - started))
                if parsed is not None:
                    record['citation_audit'] = audit_ids(pair['diff'], parsed['evidence_ids'])
            except Exception as error:
                record['transport_error'] = repr(error)
            with result_path.open('a') as stream:
                stream.write(json.dumps(record, ensure_ascii=False) + '\n')
                stream.flush()
                os.fsync(stream.fileno())
            index[pair['id'], arm] = record
            progress = {'model': model['id'], 'completed': len(index), 'expected': len(pairs) * len(ARMS),
                        'pair_id': pair['id'], 'arm': arm, 'updated_unix': time.time()}
            write_json(HERE / 'progress.json', progress)
            if len(index) % 30 == 0 or record.get('transport_error'):
                print(json.dumps(progress), flush=True)
            if record.get('transport_error'):
                raise RuntimeError(record['transport_error'])
            assert record['usage']['prompt_tokens'] == len(ids)
