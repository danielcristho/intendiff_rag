"""Usage: python pipeline/extension_audit.py --release DIR."""
import argparse
import hashlib
import json
import math
import sys
from collections.abc import Mapping
from pathlib import Path


def context_settings(config, maximum):
    context = max(32768, math.ceil((maximum + 512) / 1024) * 1024)
    if context > config['max_position_embeddings']:
        raise ValueError('Identical input exceeds native context; no pair may be dropped')
    head = config.get('head_dim') or config['hidden_size'] // config['num_attention_heads']
    bytes_per_token = 2 * 2 * config['num_hidden_layers'] * config['num_key_value_heads'] * head
    cache = max(6 * 1024**3, math.ceil(context * bytes_per_token / 1024**3) * 1024**3)
    return dict(max_model_len=context, kv_cache_memory_bytes=cache)


def token_count(tokenizer, messages, options):
    encoded = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True, **options)
    ids = encoded['input_ids'] if isinstance(encoded, Mapping) else encoded
    if not isinstance(ids, list) or not ids or any(type(t) is not int for t in ids):
        raise ValueError('Expected one flat chat token list')
    return len(ids)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--release', type=Path, required=True)
    args = parser.parse_args()
    out = args.release
    sys.path.insert(0, str(out / 'code'))
    from configs import CONFIGS
    from prompts import build, card_block
    from runner import retrieve
    from retrieval_audit import audit_retrieval
    from samples import load_jsonl
    from transformers import AutoTokenizer
    model = json.loads((out / 'model.json').read_text())
    tokenizer = AutoTokenizer.from_pretrained(model['path'], local_files_only=True, trust_remote_code=False)
    cards = load_jsonl(out / 'kb.jsonl')
    lengths = [dict(id=c['id'], card_tokens=len(tokenizer.encode(card_block(1, c), add_special_tokens=False)),
                    intent_tokens=len(tokenizer.encode(c['intent'], add_special_tokens=False))) for c in cards]
    maximum, stages = 0, {}
    for stage in ('dev', 'test'):
        pairs = load_jsonl(out / f'{stage}.pairs.jsonl')
        issues, plan = audit_retrieval(pairs, cards, list(CONFIGS), retrieve)
        if issues:
            raise ValueError(str(issues))
        rows = []
        for pair in pairs:
            for config in CONFIGS:
                messages = build(config, pair, retrieve(config, pair, cards))
                tokens = token_count(tokenizer, messages, model['chat_template_kwargs'])
                maximum = max(maximum, tokens)
                rows.append(dict(model=model['id'], pair_id=pair['id'], config=config, prompt_tokens=tokens,
                                 messages_sha256=hashlib.sha256(json.dumps(messages, sort_keys=True).encode()).hexdigest()))
        (out / f'{stage}.prompt-tokens.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in rows))
        stages[stage] = dict(pairs=len(pairs), requests=len(rows), max_prompt_tokens=max(r['prompt_tokens'] for r in rows))
        print(json.dumps(dict(model=model['tag'], stage=stage, **stages[stage])), flush=True)
    config = json.loads((Path(model['path']) / 'config.json').read_text())
    result = dict(ready=True, model=model['id'], stages=stages, card_token_counts=lengths,
                  cards_over_original_token_limit=sum(r['card_tokens'] > 512 or r['intent_tokens'] > 64 for r in lengths),
                  text_policy='Identical frozen D101 text; original construction limits use Qwen tokenizers',
                  **context_settings(config, maximum))
    (out / 'budget.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'card_token_counts'}), flush=True)


if __name__ == '__main__':
    main()
