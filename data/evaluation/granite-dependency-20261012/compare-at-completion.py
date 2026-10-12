"""Compare paired model decisions without claiming unverified accuracy or FPR."""
import csv
import json
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
HERE=ROOT/'data/evaluation/granite-dependency-20261012'
read=lambda p:[json.loads(x) for x in p.read_text().splitlines()]
old=read(HERE/'qwen-historical-results.jsonl');new=read(HERE/'results.jsonl')
state=lambda r:r['parsed']['verdict'] if r['json_valid'] else 'invalid'
index={(r['pair_id'],r['arm']):r for r in old}
assert len(new)==len(old)==len(index)==30
cases=[]
for r in new:
 prior=index[r['pair_id'],r['arm']]
 cases.append({'pair_id':r['pair_id'],'cohort':r['cohort'],'arm':r['arm'],
               'qwen':state(prior),'granite':state(r),'changed':state(prior)!=state(r),
               'qwen_reason':(prior['parsed'] or {}).get('reason'),
               'granite_reason':(r['parsed'] or {}).get('reason')})
groups=[];transitions=[]
for cohort in ('HN','MAL'):
 for arm in ('NO-SOURCE','WITH-SOURCE'):
  selected=[r for r in cases if r['cohort']==cohort and r['arm']==arm]
  groups.append({'cohort':cohort,'arm':arm,'n':len(selected),
                 'qwen':dict(Counter(r['qwen'] for r in selected)),
                 'granite':dict(Counter(r['granite'] for r in selected)),'FPR':None,'gold_accuracy':None})
  transitions += [{'cohort':cohort,'arm':arm,'qwen':a,'granite':b,'n':n} for (a,b),n in
                  Counter((r['qwen'],r['granite']) for r in selected).items()]
result={'groups':groups,'transitions':transitions,'changed_decisions':sum(r['changed'] for r in cases),
        'new_total_tokens':sum(r['usage']['prompt_tokens']+r['usage']['completion_tokens'] for r in new),
        'historical_total_tokens':sum(r['usage']['prompt_tokens']+r['usage']['completion_tokens'] for r in old),
        'claim_scope':'exploratory paired model comparison; not gold accuracy, FPR or causal size effect'}
(HERE/'comparison.json').write_text(json.dumps(result,indent=2)+'\n')
with (HERE/'comparison-cases.csv').open('w') as stream:
 writer=csv.DictWriter(stream,fieldnames=list(cases[0]));writer.writeheader();writer.writerows(cases)
print(json.dumps(result,indent=2))
