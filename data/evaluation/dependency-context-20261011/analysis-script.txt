"""Describe post-hoc citation coverage and cost against the historical IDS-I subgroup."""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'data/evaluation/dependency-context-20261011'
rows = [json.loads(line) for line in (HERE / 'results.jsonl').read_text().splitlines()]
targets = {r['pair_id'] for r in rows}
old = [json.loads(line) for line in (HERE.parent / 'mixed-validation-20261011/results.jsonl').read_text().splitlines()]
old = [r for r in old if r['pair_id'] in targets and r['arm'] == 'IDS-I']
assert len(old) == 20 and all(r['json_valid'] and r['parsed']['verdict'] == 'benign' for r in old)
baseline_tokens = sum(r['usage']['prompt_tokens'] + r['usage']['completion_tokens'] for r in old)
groups = []
for arm in ('CTX-1.11.21', 'CTX-1.11.22'):
    selected = [r for r in rows if r['arm'] == arm]
    citations = [c for r in selected for c in r.get('citation_audit', {}).get('referenced_lines', [])]
    setup = [r['pair_id'] for r in selected if any(c['source'] == 'dependency_context' and c['path'] == 'setup.cjs'
             for c in r.get('citation_audit', {}).get('referenced_lines', []))]
    tokens = sum(r['usage']['prompt_tokens'] + r['usage']['completion_tokens'] for r in selected)
    groups.append({'arm': arm, 'total_tokens': tokens, 'ratio_to_historical_IDS_I_tokens': tokens / baseline_tokens,
                   'responses_citing_setup_content': len(setup),
                   'pair_ids_without_setup_content_citation': [r['pair_id'] for r in selected if r['pair_id'] not in setup],
                   'dependency_content_citing_responses': sum(any(c['source'] == 'dependency_context' and c['path'] is not None
                       for c in r.get('citation_audit', {}).get('referenced_lines', [])) for r in selected),
                   'citation_breakdown': [{'source': s, 'path': p, 'kind': k, 'n': n} for (s,p,k),n in
                       Counter((c['source'], c['path'], c['kind']) for c in citations).items()]})
result = {'analysis_scope': 'post_hoc_descriptive', 'historical_IDS_I_total_tokens': baseline_tokens,
          'new_total_tokens': sum(g['total_tokens'] for g in groups), 'groups': groups,
          'semantic_support_verified': False,
          'warning': 'Known citation IDs and positive verdicts do not validate every reason claim.'}
(HERE / 'diagnostics.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
