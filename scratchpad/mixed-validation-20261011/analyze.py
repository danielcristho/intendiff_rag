"""Compute observed costs, citation diagnostics, and source-label misses for D87."""
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'data/evaluation/mixed-validation-20261011'
read = lambda name: [json.loads(line) for line in (HERE / name).open()]
rows = read('results.jsonl')
pairs = {p['id']: p for p in read('pairs.jsonl')}
index = {(r['pair_id'], r['arm']): r for r in rows}
assert len(rows) == len(index) == 160
misses, citations, costs = [], [], []
for row in rows:
    if not row['json_valid'] or row['parsed']['verdict'] != 'malicious':
        misses.append({'pair_id': row['pair_id'], 'arm': row['arm'],
                       'state': row['parsed']['verdict'] if row['json_valid'] else 'invalid',
                       'parsed': row['parsed'], 'campaign': pairs[row['pair_id']]['campaign'],
                       'interpretation': 'Miss relative to upstream MAL label, not independently verified FN'})
    audit = row.get('citation_audit')
    if audit:
        noncontent = [x for x in audit['referenced_lines'] if x['kind'] in ('metadata', 'hunk')]
        if noncontent or audit['unknown_ids']:
            citations.append({'pair_id': row['pair_id'], 'arm': row['arm'],
                              'parsed': row['parsed'], 'citation_audit': audit})
for arm in ('LEGACY-I', 'SCHEMA-I', 'IDS-I', 'IDS-D', 'VERIFY-I'):
    selected = [r for r in rows if r['arm'] == arm]
    latency = sorted(r['latency_ms'] for r in selected)
    costs.append({'arm': arm, 'input_tokens': sum(r['usage']['prompt_tokens'] for r in selected),
                  'output_tokens': sum(r['usage']['completion_tokens'] for r in selected),
                  'median_latency_ms': statistics.median(latency),
                  'p95_nearest_rank_latency_ms': latency[30]})
combined = [index[pid, 'IDS-I']['latency_ms'] + index[pid, 'VERIFY-I']['latency_ms'] for pid in pairs]
tokens = lambda arms: sum(r['usage']['total_tokens'] for r in rows if r['arm'] in arms)
result = {'new_mal_generations': 160, 'costs': costs, 'token_total': tokens({r['arm'] for r in rows}),
          'two_stage_tokens': tokens({'IDS-I', 'VERIFY-I'}),
          'two_stage_relative_to_ids_i': tokens({'IDS-I', 'VERIFY-I'}) / tokens({'IDS-I'}),
          'two_stage_median_latency_ms': statistics.median(combined),
          'max_actual_prompt_tokens': max(r['usage']['prompt_tokens'] for r in rows),
          'citation_issue_responses': len(citations), 'human_gold': False}
(HERE / 'costs-and-diagnostics.json').write_text(json.dumps(result, indent=2) + '\n')
for filename, records in [('source-label-misses.jsonl', misses), ('citation-issues.jsonl', citations)]:
    (HERE / filename).write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in records))
print(json.dumps(result, indent=2))
