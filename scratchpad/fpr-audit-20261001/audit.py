"""Reproduce paired TYP transitions without inference or relabeling."""
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'data/evaluation/model-families-20261001'
OUT = Path(__file__).resolve().parent
paths = [SOURCE / name for name in ['pairs.jsonl', 'results.all-models.jsonl']]
pairs, rows = [[json.loads(line) for line in path.open()] for path in paths]
index = {(r['model'], r['config'], r['pair_id']): r for r in rows}
assert len(index) == len(rows) == 11676
typ = [p for p in pairs if p['subset'] == 'TYP']
assert len(typ) == 100
models = sorted({r['model'] for r in rows})
transitions, changed = [], []
for model in models:
    counts = Counter()
    for pair in typ:
        before, after = [index[model, c, pair['id']] for c in ['DIFF', 'DIFF+I']]
        states = tuple(r['verdict'] if r['json_valid'] else 'invalid'
                       for r in [before, after])
        counts[states] += 1
        if states in [('benign', 'malicious'), ('malicious', 'benign')]:
            changed.append({'model': model, 'pair_id': pair['id'],
                            'transition': list(states),
                            'before_reason': before['reason'],
                            'after_reason': after['reason'],
                            'intent': pair['intent'], 'diff': pair['diff']})
    assert sum(counts.values()) == 100
    fp_before = sum(n for (a, b), n in counts.items() if a == 'malicious')
    fp_after = sum(n for (a, b), n in counts.items() if b == 'malicious')
    valid_net = counts['benign', 'malicious'] - counts['malicious', 'benign']
    invalid_net = counts['invalid', 'malicious'] - counts['malicious', 'invalid']
    assert fp_after - fp_before == valid_net + invalid_net
    transitions.append({'model': model, 'fp_before': fp_before,
                        'fp_after': fp_after, 'both_valid_net': valid_net,
                        'any_invalid_net': invalid_net,
                        'transitions': [{'before': a, 'after': b, 'n': n}
                                        for (a, b), n in sorted(counts.items())]})
result = {
    'scope': 'Exploratory source-labeled TYP audit; not human gold or causal attribution.',
    'new_llm_calls': 0,
    'n_typ': len(typ), 'invalid_policy': 'benign',
    'source_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in paths},
    'intent_missing_including_sentinel': {
        k: sum(p['intent'].get(k) in [None, '', 'not available'] for p in typ)
        for k in ['description', 'keywords', 'scripts', 'readme']},
    'models': transitions,
}
(OUT / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
(OUT / 'valid-verdict-changes.jsonl').write_text(
    ''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in changed))
print(json.dumps({'models': transitions, 'changed_valid_pairs': len(changed)}, indent=2))
