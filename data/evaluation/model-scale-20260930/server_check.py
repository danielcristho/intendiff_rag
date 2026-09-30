"""Verify the server renders real messages identically to the pinned tokenizer."""
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

from prompts import build

HERE = Path(__file__).resolve().parent
model_id = sys.argv[1]
pairs = list(map(json.loads, (HERE / 'pairs.jsonl').open()))
audited = {(r['config'], r['pair_id']): r for r in
           map(json.loads, (HERE / 'context-audit.jsonl').open()) if r['model'] == model_id}
checks = []
for config in ['DIFF', 'DIFF+I']:
    pair = max(pairs, key=lambda p: audited[config, p['id']]['prompt_tokens'])
    expected = audited[config, pair['id']]
    payload = {'model': model_id, 'messages': build(config, pair),
               'add_generation_prompt': True, 'chat_template_kwargs': expected['chat_template_kwargs']}
    request = urllib.request.Request('http://127.0.0.1:8101/tokenize',
                                     data=json.dumps(payload).encode(),
                                     headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(request, timeout=60) as response:
        result = json.load(response)
    digest = hashlib.sha256(json.dumps(result['tokens'], separators=(',', ':')).encode()).hexdigest()
    assert result['count'] == expected['prompt_tokens'] and digest == expected['token_ids_sha256']
    assert result['max_model_len'] == 32768
    checks.append({'config': config, 'pair_id': pair['id'], 'tokens': result['count'],
                   'token_ids_match': True})
model = next(m for m in json.loads((HERE / 'models.json').read_text()) if m['id'] == model_id)
summary = {'verified': True, 'model': model_id, 'tokenization_requests': 2,
           'new_llm_calls': 0, 'checks': checks}
(HERE / f'{model["tag"]}.server-check.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps(summary), flush=True)
