"""Describe development costs and paired changes without inferring gold labels."""
import json
import statistics
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'data/evaluation/evidence-dev-20261001'
pairs = {p['id']: p for p in map(json.loads, (HERE / 'pairs.jsonl').open())}
rows = [json.loads(l) for l in (HERE / 'results.jsonl').open()]
index = {(r['pair_id'], r['arm']): r for r in rows}
assert len(rows) == len(index) == 160
arms = ['LEGACY-I', 'SCHEMA-I', 'IDS-I', 'IDS-D', 'VERIFY-I']
costs = []
for arm in arms:
    selected = [r for r in rows if r['arm'] == arm]
    latencies = [r['latency_ms'] for r in selected]
    costs.append({'arm': arm, 'total_tokens': sum(r['usage']['total_tokens'] for r in selected),
                  'median_latency_ms': statistics.median(latencies),
                  'p95_latency_ms': float(np.percentile(latencies, 95)),
                  'sum_request_latency_ms': sum(latencies)})
latencies = [index[pid, 'IDS-I']['latency_ms'] + index[pid, 'VERIFY-I']['latency_ms'] for pid in pairs]
costs.append({'arm': 'IDS-I plus VERIFY-I',
              'total_tokens': sum(c['total_tokens'] for c in costs if c['arm'] in ['IDS-I', 'VERIFY-I']),
              'median_latency_ms': statistics.median(latencies),
              'p95_latency_ms': float(np.percentile(latencies, 95)),
              'sum_request_latency_ms': sum(latencies)})
changes = []
for before, after in [('LEGACY-I', 'SCHEMA-I'), ('SCHEMA-I', 'IDS-I'), ('IDS-D', 'IDS-I'), ('IDS-I', 'VERIFY-I')]:
    for pid, pair in pairs.items():
        a, b = index[pid, before], index[pid, after]
        old = a['parsed']['verdict'] if a['json_valid'] else 'invalid'
        new = b['parsed']['verdict'] if b['json_valid'] else 'invalid'
        if old != new:
            changes.append({'pair_id': pid, 'before_arm': before, 'after_arm': after,
                            'before_state': old, 'after_state': new,
                            'before_parsed': a['parsed'], 'after_parsed': b['parsed'],
                            'after_citation_audit': b.get('citation_audit'),
                            'human_annotation_verified': False})
issues = []
for row in rows:
    audit = row.get('citation_audit')
    if audit and (audit['unknown_ids'] or audit['duplicate_ids'] or
                  audit['content_line_count'] == 0 or any(
                      r['kind'] in ['metadata', 'hunk'] for r in audit['referenced_lines'])):
        issues.append({'pair_id': row['pair_id'], 'arm': row['arm'],
                       'parsed': row['parsed'], 'citation_audit': audit})
report = {'scope': 'Post hoc descriptive development analysis; no class labels assigned',
          'costs': costs, 'changed_states': len(changes),
          'citation_issue_responses': len(issues),
          'max_actual_prompt_tokens': max(r['usage']['prompt_tokens'] for r in rows),
          'total_prompt_tokens': sum(r['usage']['prompt_tokens'] for r in rows),
          'total_completion_tokens': sum(r['usage']['completion_tokens'] for r in rows)}
(HERE / 'costs-and-diagnostics.json').write_text(json.dumps(report, indent=2) + '\n')
for name, records in [('paired-changes.jsonl', changes), ('citation-issues.jsonl', issues)]:
    (HERE / name).write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in records))
print(json.dumps(report, indent=2))
