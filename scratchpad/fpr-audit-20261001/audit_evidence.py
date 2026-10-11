"""Audit literal evidence provenance in all historical outputs without relabeling."""
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'pipeline'))
from evidence import index_diff

SOURCE = ROOT / 'data/evaluation/model-families-20261001'
OUT = Path(__file__).resolve().parent
pairs = {p['id']: p for p in map(json.loads, (SOURCE / 'pairs.jsonl').open())}
rows = [json.loads(l) for l in (SOURCE / 'results.all-models.jsonl').open()]
indexes = {pid: index_diff(p['diff']) for pid, p in pairs.items()}
groups = defaultdict(Counter)
exceptions = []
for row in rows:
    pair = pairs[row['pair_id']]
    group = groups[row['model'], row['config'], pair['subset']]
    group['responses'] += 1
    if not row['json_valid']:
        group['invalid'] += 1
        continue
    group['valid'] += 1
    lines = indexes[pair['id']]
    exact = defaultdict(list)
    stripped = defaultdict(list)
    for line in lines:
        exact[line['text']].append(line)
        stripped[line['text'].strip()].append(line)
        if line['kind'] in ['added', 'deleted', 'context']:
            stripped[line['text'][1:].strip()].append(line)
    statuses = []
    for citation in row['evidence']:
        if citation in exact:
            status = 'exact_line'
        elif citation.strip() in stripped:
            status = 'whitespace_or_diff_marker_normalized'
        else:
            status = 'not_a_complete_line'
        statuses.append(status)
        group['citations_' + status] += 1
    missing = 'not_a_complete_line' in statuses
    empty = not statuses
    group['responses_with_unmatched_citation'] += missing
    group['responses_with_empty_evidence'] += empty
    if row['verdict'] == 'malicious':
        group['malicious_predictions'] += 1
        group['malicious_with_unmatched_citation'] += missing
        group['malicious_with_empty_evidence'] += empty
    if missing:
        exceptions.append({'model': row['model'], 'config': row['config'],
                           'pair_id': pair['id'], 'subset': pair['subset'],
                           'verdict': row['verdict'], 'evidence': row['evidence'],
                           'citation_statuses': statuses})
result = {'responses': len(rows), 'new_llm_calls': 0,
          'scope': 'Literal provenance only; unmatched includes substrings/multiline citations, not necessarily hallucination.',
          'interpretation': 'Neither exact text nor a valid line ID establishes semantic correctness. No labels or verdicts changed.',
          'source_sha256': {name: hashlib.sha256((SOURCE / name).read_bytes()).hexdigest()
                            for name in ['pairs.jsonl', 'results.all-models.jsonl']},
          'groups': [dict(model=m, config=c, subset=s, **dict(counts))
                     for (m, c, s), counts in sorted(groups.items())]}
(OUT / 'evidence-provenance.json').write_text(json.dumps(result, indent=2) + '\n')
(OUT / 'unmatched-evidence.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in exceptions))
print(json.dumps([g for g in result['groups'] if g['subset'] == 'TYP'], indent=2))
