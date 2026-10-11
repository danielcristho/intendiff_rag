"""Recount DIFF to DIFF+I transitions without repairing invalid predictions."""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
reports = []
for folder in ('source-baselines-20260929', 'output-budget-20260929',
               'model-scale-20260930', 'model-families-20261001'):
    here = ROOT / 'data/evaluation' / folder
    rows = [json.loads(line) for line in (here / 'results.jsonl').open()]
    pairs = [json.loads(line) for line in (here / 'pairs.jsonl').open()]
    index = {(r['model'], r['config'], r['pair_id']): r for r in rows}
    for model in sorted({r['model'] for r in rows}):
        subsets = {}
        for subset in ('MAL', 'TYP'):
            transitions = Counter()
            valid_net = invalid_net = 0
            for pair in pairs:
                if pair['subset'] != subset:
                    continue
                a, b = (index[model, config, pair['id']] for config in ('DIFF', 'DIFF+I'))
                av, bv = (r['verdict'] if r['json_valid'] else 'invalid' for r in (a, b))
                transitions[av + '->' + bv] += 1
                net = int(bv == 'malicious') - int(av == 'malicious')
                if a['json_valid'] and b['json_valid']:
                    valid_net += net
                else:
                    invalid_net += net
            subsets[subset] = {'transitions': dict(transitions), 'valid_net': valid_net,
                               'invalid_net': invalid_net}
        reports.append({'experiment': folder, 'model': model, 'subsets': subsets})
(OUT / 'intent-transitions.json').write_text(json.dumps(reports, indent=2) + '\n')
print(f'Checked {len(reports)} paired model comparisons')
