"""Record cohort limitations, citation coverage, costs and missing source priorities."""
import json
from collections import Counter,defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
HERE=ROOT/'data/evaluation/dependency-generalization-20261012'
read=lambda p:[json.loads(x) for x in p.read_text().splitlines()]
rows=read(HERE/'results.jsonl');pairs=read(HERE/'pairs.jsonl')
snapshots=json.loads((HERE/'context-snapshots.json').read_text())
tokens={arm:sum(r['usage']['prompt_tokens']+r['usage']['completion_tokens'] for r in rows if r['arm']==arm) for arm in ('NO-SOURCE','WITH-SOURCE')}
reasons=read(HERE/'selection-exclusions.jsonl')
future=[r for r in reasons if r['reason']=='future_or_missing_timestamp']
missing=defaultdict(list)
local_names={r['name'] for r in read(ROOT/'data/acquisition/extracted.typical.jsonl')+read(ROOT/'data/acquisition/datadog.inventory-full.jsonl')}
for p in read(ROOT/'data/acquisition/pairs.preprocessed-v2.jsonl'):
    if p['subset']!='MAL' or p.get('truncated'):
        continue
    dependencies=(p.get('delta_evidence') or {}).get('dependency_change',[])
    if any(d['dependency']=='easy-day-js' for d in dependencies):
        continue
    for d in dependencies:
        if d['dependency'] not in local_names:
            missing[d['dependency']].append({'pair_id':p['id'],'constraint':d['after'],'target_published':p.get('published_at')})
priorities=[{'dependency':name,'target_count':len(targets),'targets':targets,'status':'source_absent_from_local_inventories','not_inference_results':True}
            for name,targets in sorted(missing.items(),key=lambda kv:(-len(kv[1]),kv[0]))]
(HERE/'missing-dependency-sources.json').write_text(json.dumps(priorities,indent=2)+'\n')
result={'analysis_scope':'post_hoc_descriptive','tokens':tokens,'total_new_tokens':sum(tokens.values()),
        'context_token_ratio':tokens['WITH-SOURCE']/tokens['NO-SOURCE'],
        'HN_delta_patterns':dict(Counter(','.join(p['delta']) for p in pairs if p['subset']=='HN')),
        'dependency_snapshots_with_install_hook':sum(any(k in json.loads(s['files']['package.json']).get('scripts',{})
             for k in ('preinstall','install','postinstall')) for s in snapshots.values()),
        'selected_prior_D86_dev':sum(r['previous_D86_dev'] for r in read(HERE/'dev-exclusions.jsonl')),
        'future_version_exclusions':sum(all(r['times']) for r in future),
        'missing_timestamp_exclusions':sum(not all(r['times']) for r in future),
        'semantic_support_verified':False,
        'dependency_content_citing_pairs':[r['pair_id'] for r in rows if r.get('citation_audit',{}).get('dependency_content_citations',0)>0]}
(HERE/'diagnostics.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2));print('Missing source priorities:',[(r['dependency'],r['target_count']) for r in priorities[:6]])
