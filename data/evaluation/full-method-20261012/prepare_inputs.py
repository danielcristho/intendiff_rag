"""Audit every prompt and apply one common line-prefix budget before inference."""
import copy
import hashlib
import json

from transformers import AutoTokenizer
from common import HERE, read_rows, token_ids, write_json
from prompts import build


def main():
    assert not (HERE / 'protocol.json').exists(), 'Frozen inputs cannot be regenerated'
    models = json.loads((HERE / 'models.json').read_text())
    tokenizers = [AutoTokenizer.from_pretrained(m['path'], local_files_only=True,
                  trust_remote_code=False) for m in models]
    pairs = read_rows(HERE / 'original-pairs.jsonl')
    assert len(pairs) == len({p['id'] for p in pairs}) == 973
    outputs, changes, audit = [], [], []
    for n, original in enumerate(pairs, 1):
        pair = copy.deepcopy(original)
        lines = pair['diff'].splitlines()

        def counts(keep):
            candidate = dict(pair, diff='\n'.join(lines[:keep]) if keep < len(lines) else pair['diff'])
            return {(m['tag'], a): len(token_ids(t, m, build(a, candidate)))
                    for m, t in zip(models, tokenizers) for a in ['IDS-D', 'IDS-I']}

        lengths = counts(len(lines))
        original_max = max(lengths.values())
        keep = len(lines)
        # Reserve 4K for the verifier instruction and serialized 2K-token candidate.
        if original_max > 26624:
            low, high = 0, len(lines)
            assert max(counts(0).values()) <= 26624, 'Intent alone exceeds common budget'
            while low < high:
                middle = (low + high + 1) // 2
                if max(counts(middle).values()) <= 26624:
                    low = middle
                else:
                    high = middle - 1
            keep = low
            pair['diff'] = '\n'.join(lines[:keep])
            pair['truncated'] = True
            lengths = counts(keep)
        pair['diff_sha256'] = hashlib.sha256(pair['diff'].encode()).hexdigest()
        pair['full_method_additional_truncation'] = keep < len(lines)
        outputs.append(pair)
        changes.append({'pair_id': pair['id'], 'original_lines': len(lines), 'kept_lines': keep,
                        'original_max_prompt_tokens': original_max,
                        'final_max_prompt_tokens': max(lengths.values()),
                        'original_diff_sha256': original['diff_sha256'],
                        'final_diff_sha256': pair['diff_sha256']})
        audit.extend({'pair_id': pair['id'], 'model_tag': tag, 'arm': arm, 'prompt_tokens': count}
                     for (tag, arm), count in lengths.items())
        if n % 50 == 0 or n == len(pairs):
            print(json.dumps({'audited_pairs': n, 'expected': len(pairs)}), flush=True)
    for name, records in [('pairs.jsonl', outputs), ('input-budget.jsonl', changes),
                          ('token-audit.jsonl', audit)]:
        (HERE / name).write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in records))
    write_json(HERE / 'input-summary.json', {'pairs': len(outputs), 'models': len(models),
        'additional_truncated_pairs': sum(r['kept_lines'] < r['original_lines'] for r in changes),
        'base_prompt_budget': 26624, 'verifier_reserve_tokens': 4096, 'output_tokens': 2048,
        'dropped_pairs': 0, 'maximum_final_base_prompt_tokens': max(r['prompt_tokens'] for r in audit)})


if __name__ == '__main__':
    main()
