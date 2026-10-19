"""Verify requests, temporal provenance, source bytes and reported D90 counts."""
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path
import jsonschema
from transformers import AutoTokenizer

ROOT=Path(__file__).resolve().parents[2]
HERE=ROOT/'data/evaluation/granite-dependency-20261012'
sys.path.insert(0,str(HERE))
from evaluate import verify
from prompts import ARMS, IDS_SCHEMA, build, audit
from selection import precedes, rank

read=lambda path:[json.loads(x) for x in path.read_text().splitlines()]
protocol=json.loads((HERE/'protocol.json').read_text());verify(protocol)
pairs={p['id']:p for p in read(HERE/'pairs.jsonl')}
pool={p['id']:p for p in read(ROOT/'data/acquisition/pairs.preprocessed-v2.jsonl')}
snapshots=json.loads((HERE/'context-snapshots.json').read_text())
for pair in pairs.values():
    assert pair==pool[pair['id']]
    assert hashlib.sha256(pair['diff'].encode()).hexdigest()==pair['diff_sha256']
for row in read(HERE/'selection-audit.jsonl'):
    p=row['provenance'];snapshot=snapshots[row['pair_id']]
    assert precedes(p['dependency_published'],p['target_published'])
    for name,expected in p['files'].items():
        assert hashlib.sha256(snapshot['files'][name].encode()).hexdigest()==expected
assert len({s['name'] for s in snapshots.values()})==len(pairs)==15
rows=read(HERE/'results.jsonl');index={(r['pair_id'],r['arm']):r for r in rows}
assert len(rows)==len(index)==protocol['expected_generations']==30
assert set(index)=={(p,a) for p in pairs for a in ARMS}
expected_order=[(p,a) for p in pairs for a in (ARMS if int(rank(p),16)%2==0 else list(reversed(ARMS)))]
assert [(r['pair_id'],r['arm']) for r in rows]==expected_order
assert len({r['response_id'] for r in rows})==30
model=protocol['model'];tokenizer=AutoTokenizer.from_pretrained(model['path'],local_files_only=True,trust_remote_code=False)
for row in rows:
    pair,snapshot=pairs[row['pair_id']],snapshots[row['pair_id']]
    messages=build(row['arm'],pair,snapshot)
    payload={'model':model['id'],'messages':messages,'temperature':0,'top_p':1,'seed':0,'max_tokens':2048,'chat_template_kwargs':{'thinking':False},'stop_token_ids':[0],
             'response_format':{'type':'json_schema','json_schema':{'name':'decision','strict':True,'schema':IDS_SCHEMA}}}
    assert hashlib.sha256(json.dumps(payload).encode()).hexdigest()==row['request_sha256']
    ids=tokenizer.apply_chat_template(messages,tokenize=True,add_generation_prompt=True,thinking=False)['input_ids']
    assert len(ids)==row['expected_prompt_tokens']==row['usage']['prompt_tokens']
    assert len(ids)+2048<=32768 and 0<row['usage']['completion_tokens']<=2048
    parsed=None
    if row['finish_reason']!='length':
        try:
            obj,_=json.JSONDecoder().raw_decode(row['raw'][row['raw'].index('{'):])
            jsonschema.validate(obj,IDS_SCHEMA);parsed=obj
        except (ValueError,jsonschema.ValidationError):
            pass
    assert parsed==row['parsed'] and (parsed is not None)==row['json_valid']
    if parsed:
        assert audit(row['arm'],pair,snapshot,parsed['evidence_ids'])==row['citation_audit']
    assert row['cohort']==pair['subset'] and row['conditional_version']==snapshot['version']
    assert row['human_annotation_verified'] is False and row['actual_installed_version_verified'] is False
    assert not row.get('transport_error')
summary=json.loads((HERE/'summary.json').read_text())
for group in summary['groups']:
    selected=[r for r in rows if r['arm']==group['arm'] and r['cohort']==group['cohort']]
    counts=Counter(r['parsed']['verdict'] if r['json_valid'] else 'invalid' for r in selected)
    assert group['verdicts']==counts and group['n']==len(selected)
    assert group['FPR'] is None and group['gold_accuracy'] is None
    for field in ('prompt_tokens','completion_tokens'):
        assert group[field]==sum(r['usage'][field] for r in selected)
log=(HERE/'server.log').read_text()
statuses=Counter(re.findall(r'POST /v1/chat/completions HTTP/1\.1" (\d+)',log))
assert statuses=={'200':30}
assert log.count('POST /tokenize HTTP/1.1" 200 OK')==2
assert 'Application shutdown complete' in log
assert json.loads((HERE/'status.json').read_text())['stage']=='complete'
result={'verified':True,'new_generations':30,'pairs':15,'request_hashes_tokens_parsing_citations_match':True,
        'source_inputs_and_temporal_checks_match':True,'arm_order_counterbalance_matches':True,
        'http_generation_statuses':dict(statuses),'server_shutdown_complete':True,
        'frozen_hash_counts':{k:len(protocol[k]) for k in ('source_sha256','upstream_sha256','model_sha256')},
        'human_gold_verified':False,'installed_versions_verified':False,'FPR_available':False,'RAG_evaluated':False}
(HERE/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
