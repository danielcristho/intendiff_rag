"""Usage: python pipeline/source_budget.py --pairs FILE --kb FILE --out DIR."""
import argparse
import hashlib
import json
from collections import Counter
from collections.abc import Mapping
from pathlib import Path

from configs import CONFIGS
from label_provenance import validate
from prompts import build
from retrieval_audit import audit_retrieval
from runner import retrieve
from samples import load_jsonl
from source_cards import verify
from wyss import write_jsonl


def chat_tokens(tokenizer, messages):
    encoded = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True)
    # Transformers versions differ: newer releases return a BatchEncoding mapping.
    ids = encoded['input_ids'] if isinstance(encoded, Mapping) else encoded
    if not isinstance(ids, list) or not ids or any(type(token) is not int for token in ids):
        raise ValueError('Expected one flat token ID list from the chat template')
    return len(ids)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pairs', type=Path, required=True)
    parser.add_argument('--kb', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    pairs, cards = load_jsonl(args.pairs), load_jsonl(args.kb)
    issues, plan = audit_retrieval(pairs, cards, list(CONFIGS), retrieve)
    sources = {}
    for pair in pairs:
        problem = validate(pair, sources)
        if problem:
            issues.append(dict(id=pair['id'], reason=problem))
        if pair.get('diff_sha256') != hashlib.sha256(pair.get('diff', '').encode()).hexdigest():
            issues.append(dict(id=pair['id'], reason='diff_hash_mismatch'))
        if pair.get('intent_from') != pair.get('before'):
            issues.append(dict(id=pair['id'], reason='intent_origin_mismatch'))
        if not pair.get('diff') or pair.get('preprocessing', {}).get('version') != 'static-dolos-exact-v2':
            issues.append(dict(id=pair['id'], reason='missing_normalized_diff'))
        if not pair.get('sha256_before') or not pair.get('sha256_after'):
            issues.append(dict(id=pair['id'], reason='missing_archive_hash'))
    write_jsonl(args.out / 'retrieval-plan.jsonl', plan)
    frozen = Path('data/evaluation/full-method-20261012/protocol.json')
    models = json.loads(frozen.read_text())['models'][:2]
    from transformers import AutoTokenizer
    token_rows, summaries = [], []
    for model in models:
        tokenizer = AutoTokenizer.from_pretrained(model['path'], local_files_only=True, trust_remote_code=False)
        count = lambda text: len(tokenizer.encode(text, add_special_tokens=False))
        for card in cards:
            problem = verify(card, count, sources)
            if problem:
                issues.append(dict(id=card['id'], model=model['id'], reason=problem))
        maximum = 0
        for pair in pairs:
            for config in CONFIGS:
                messages = build(config, pair, retrieve(config, pair, cards))
                tokens = chat_tokens(tokenizer, messages)
                maximum = max(maximum, tokens)
                token_rows.append(dict(model=model['id'], pair_id=pair['id'], config=config, prompt_tokens=tokens))
                if tokens + 512 > 32768:
                    issues.append(dict(id=pair['id'], config=config, model=model['id'], reason='prompt_budget_exceeded', tokens=tokens))
        summaries.append(dict(model=model['id'], max_prompt_tokens=maximum, output_reserved=512, context=32768))
        print(json.dumps(summaries[-1]), flush=True)
    write_jsonl(args.out / 'prompt-tokens.jsonl', token_rows)
    summary = dict(ready_for_freeze_checks=not issues, pairs=len(pairs), cards=len(cards),
                   expected_generations=len(token_rows), models=summaries, issues=issues,
                   subset_counts=dict(Counter(r.get('subset') for r in pairs)),
                   input_pins=[dict(path=str(p), sha256=hashlib.sha256(p.read_bytes()).hexdigest())
                               for p in (args.pairs, args.kb, frozen)])
    (args.out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({k: v for k, v in summary.items() if k != 'input_pins'}), flush=True)
    raise SystemExit(0 if not issues else 2)


if __name__ == '__main__':
    main()
