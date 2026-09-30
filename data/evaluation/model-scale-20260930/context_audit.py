"""Count every real prompt with each pinned tokenizer without running inference."""
import hashlib
import json
from pathlib import Path

from transformers import AutoTokenizer
from prompts import build

HERE = Path(__file__).resolve().parent
models = json.loads((HERE / 'models.json').read_text())
pairs = list(map(json.loads, (HERE / 'pairs.jsonl').open()))
assert len(pairs) == 973 and len({p['id'] for p in pairs}) == 973
rows, summaries = [], []
for model in models:
    tokenizer = AutoTokenizer.from_pretrained(model['path'], local_files_only=True,
                                             trust_remote_code=False)
    kwargs = {'enable_thinking': False} if model['enable_thinking'] is False else {}
    selected = []
    for pair in pairs:
        for config in ['DIFF', 'DIFF+I']:
            messages = build(config, pair)
            assert messages == build(config, {**pair, 'label': 'hidden-label-audit'})
            encoded = tokenizer.apply_chat_template(messages, tokenize=True,
                                                     add_generation_prompt=True, **kwargs)
            ids = encoded['input_ids']
            count = len(ids)
            assert count + 2048 <= 32768, (model['id'], config, pair['id'], count)
            row = {'model': model['id'], 'revision': model['revision'], 'config': config,
                   'pair_id': pair['id'], 'prompt_tokens': count,
                   'context_headroom_tokens': 32768 - count - 2048,
                   'prompt_messages_sha256': hashlib.sha256(json.dumps(messages).encode()).hexdigest(),
                   'token_ids_sha256': hashlib.sha256(json.dumps(ids, separators=(',', ':')).encode()).hexdigest(),
                   'chat_template_kwargs': kwargs}
            selected.append(row)
    rows.extend(selected)
    summaries.append({'model': model['id'], 'prompts': len(selected),
                      'max_prompt_tokens': max(r['prompt_tokens'] for r in selected),
                      'minimum_context_headroom_tokens': min(r['context_headroom_tokens'] for r in selected)})
(HERE / 'context-audit.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in rows))
summary = {'verified': True, 'new_llm_calls': 0, 'input_truncation_added': False,
           'groups': summaries}
(HERE / 'context-audit.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps(summary), flush=True)
