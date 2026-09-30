"""Read progress and detect transport or token-accounting failures."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parents[2] / 'data/evaluation/model-families-20261001'
status = json.loads((HERE / 'status.json').read_text())
audit = {(r['model'], r['config'], r['pair_id']): r['prompt_tokens']
         for r in map(json.loads, (HERE / 'context-audit.jsonl').open())}
rows = []
for path in HERE.glob('*.results.jsonl'):
    rows.extend(json.loads(line) for line in path.open() if line.endswith('\n'))
errors = [r for r in rows if r.get('error')]
successful = [r for r in rows if not r.get('error')]
assert all(r['prompt_tokens'] == audit[r['model'], r['config'], r['pair_id']]
           for r in successful), 'actual token counts diverge from local audit'
assert all(r['prompt_tokens'] + 2048 <= 32768 and 0 < r['completion_tokens'] <= 2048
           for r in successful), 'output or context limit failed'
print(json.dumps({'stage': status['stage'], 'model': status.get('model'),
                  'completed_total': len(successful), 'expected_total': 3892,
                  'invalid': sum(not r['json_valid'] for r in successful),
                  'transport_errors': len(errors), 'token_audit_match': True}))
