"""Summarize alarms without turning pending HN annotations into false-positive labels."""
import json
import statistics
from collections import Counter
from pathlib import Path

HERE=Path(__file__).resolve().parent

def state(row):
    return row['parsed']['verdict'] if row['json_valid'] else 'invalid'


def group(rows):
    return {'n':len(rows),'verdicts':dict(Counter(state(r) for r in rows)),
            'valid':sum(r['json_valid'] for r in rows),'length':sum(r['finish_reason']=='length' for r in rows),
            'unknown_id_responses':sum(bool(r.get('citation_audit',{}).get('unknown_ids')) for r in rows),
            'dependency_content_citing_responses':sum(r.get('citation_audit',{}).get('dependency_content_citations',0)>0 for r in rows),
            'prompt_tokens':sum(r['usage']['prompt_tokens'] for r in rows),
            'completion_tokens':sum(r['usage']['completion_tokens'] for r in rows),
            'median_latency_ms':statistics.median(r['latency_ms'] for r in rows),'FPR':None,'gold_accuracy':None}


def main():
    rows=[json.loads(x) for x in (HERE/'results.jsonl').read_text().splitlines()]
    pairs=[json.loads(x) for x in (HERE/'pairs.jsonl').read_text().splitlines()]
    arms=['NO-SOURCE','WITH-SOURCE'];index={(r['pair_id'],r['arm']):r for r in rows}
    assert len(rows)==len(index)==2*len(pairs) and set(index)=={(p['id'],a) for p in pairs for a in arms}
    assert not any(r.get('transport_error') for r in rows)
    groups=[];transitions=[]
    for cohort in sorted({p['subset'] for p in pairs}):
        for arm in arms:
            groups.append({'cohort':cohort,'arm':arm,**group([r for r in rows if r['cohort']==cohort and r['arm']==arm])})
        counts=Counter((state(index[p['id'],arms[0]]),state(index[p['id'],arms[1]])) for p in pairs if p['subset']==cohort)
        transitions += [{'cohort':cohort,'without':a,'with':b,'n':n} for (a,b),n in sorted(counts.items())]
    result={'complete':True,'generations':len(rows),'groups':groups,'transitions':transitions,
            'human_gold_verified':False,'installed_versions_verified':False,'RAG_evaluated':False}
    (HERE/'summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':
    main()
