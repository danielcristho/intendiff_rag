"""Shared frozen experiment paths, serialization, and request construction."""
import hashlib
import json
from pathlib import Path

from prompts import build, schema

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ARMS = ['IDS-D', 'IDS-I', 'VERIFY-I']


def read_rows(path):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write_json(path, value):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    temporary.replace(path)


def token_ids(tokenizer, model, messages):
    return tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True,
                                         **model['chat_template_kwargs'])['input_ids']


def payload(model, arm, pair, candidate=None):
    return {'model': model['id'], 'messages': build(arm, pair, candidate),
            'temperature': 0, 'top_p': 1, 'seed': 0, 'max_tokens': 2048,
            'chat_template_kwargs': model['chat_template_kwargs'],
            'stop_token_ids': model['stop_token_ids'],
            'response_format': {'type': 'json_schema', 'json_schema': {
                'name': 'decision', 'strict': True, 'schema': schema(arm)}}}


def request_hash(request):
    return hashlib.sha256(json.dumps(request).encode()).hexdigest()


def validate_rows(rows, model, pairs):
    expected = {(p['id'], a) for p in pairs for a in ARMS}
    seen = set()
    for row in rows:
        key = (row['pair_id'], row['arm'])
        assert key in expected and key not in seen, key
        assert row['model'] == model['id'] and row['experiment_id'] == HERE.name
        if row.get('transport_error'):
            raise RuntimeError('Recorded request failure requires an explicit recovery audit')
        seen.add(key)
    return seen
