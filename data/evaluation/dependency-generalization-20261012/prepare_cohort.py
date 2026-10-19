"""Select and audit all available conditional cases before inference."""
import hashlib
import json
import subprocess
import tarfile
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from transformers import AutoTokenizer
from selection import digest, precedes, source_files, select_distinct
from prompts import ARMS, build

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
assert not (HERE / 'protocol.json').exists(), 'Already frozen'
read = lambda p: [json.loads(x) for x in p.read_text().splitlines()]
write = lambda p, rows: p.write_text(''.join(json.dumps(r, ensure_ascii=False)+'\n' for r in rows))
pool = read(ROOT / 'data/acquisition/pairs.preprocessed-v2.jsonl')
index = defaultdict(list)
for record in read(ROOT / 'data/acquisition/extracted.typical.jsonl') + read(ROOT / 'data/acquisition/datadog.inventory-full.jsonl'):
    index[record['name']].append(record)
requests, matches = [], []
for pair in pool:
    if pair['subset'] not in ('MAL','HN') or pair.get('truncated'):
        continue
    deps = (pair.get('delta_evidence') or {}).get('dependency_change', [])
    if any(d['dependency'] == 'easy-day-js' for d in deps):
        continue
    for dependency in deps:
        for record in index[dependency['dependency']]:
            requests.append({'version': record['version'], 'range': dependency['after']})
            matches.append({'pair': pair, 'dependency': dependency, 'archive_record': record})
checks = json.loads(subprocess.check_output(['node', str(ROOT / 'scratchpad/dependency-context-20261011/semver-check.cjs')], input=json.dumps(requests).encode()))
candidates = [r for r,c in zip(matches,checks) if c['satisfies']]
assert candidates == json.loads((HERE / 'availability-candidates.json').read_text())
samples = {(r['name'],r['version']):r for r in read(ROOT / 'data/acquisition/samples.typical.jsonl')}
old = json.loads((ROOT / 'data/evaluation/dependency-context-20261011/protocol.json').read_text())
tokenizer = AutoTokenizer.from_pretrained(old['model']['path'], local_files_only=True, trust_remote_code=False)
exclusions, temporal = [], defaultdict(list)
for candidate in candidates:
    p,a = candidate['pair'], candidate['archive_record']
    times = []
    for record,version in ((p,p['after']),(a,a['version'])):
        path = HERE / 'publication-times' / (hashlib.sha256(record['name'].encode()).hexdigest()+'.json')
        times.append(json.loads(path.read_text())['time'].get(version))
    reason = 'future_or_missing_timestamp' if not precedes(times[1],times[0]) else None
    if not reason and p['name'] == a['name']:
        reason = 'self_dependency'
    if reason:
        exclusions.append({'pair_id':p['id'],'dependency':a['name'],'version':a['version'],'reason':reason,'times':times})
        continue
    temporal[p['id'],a['name']].append({**candidate,'target_published':times[0],'dependency_published':times[1]})
ready = []
for group in temporal.values():
    latest = max(group, key=lambda c:(c['dependency_published'],c['archive_record']['version']))
    for other in group:
        if other is not latest:
            exclusions.append({'pair_id':other['pair']['id'],'dependency':other['archive_record']['name'],
                               'version':other['archive_record']['version'],'reason':'older_local_candidate'})
    p,a = latest['pair'],latest['archive_record']
    try:
        files = source_files(ROOT / a['dir'])
        manifest = json.loads((ROOT / p['after_dir'] / 'package.json').read_text())
        sections = [s for s in ('dependencies','devDependencies','optionalDependencies','peerDependencies')
                    if manifest.get(s,{}).get(a['name']) == latest['dependency']['after']]
        assert sections
        snapshot = {'name':a['name'],'version':a['version'],'sections':sections,'files':files}
        tokens = {arm:len(tokenizer.apply_chat_template(build(arm,p,snapshot),tokenize=True,add_generation_prompt=True)['input_ids']) for arm in ARMS}
        if max(tokens.values()) + 2048 > 32768:
            raise ValueError('Context exceeds frozen budget')
        archive = a.get('archive') or samples[a['name'],a['version']]['tarball']
        assert digest(ROOT / archive) == a['sha256']
        if archive.endswith('.zip'):
            with zipfile.ZipFile(ROOT / archive) as z:
                for name,raw in files.items():
                    entries=[n for n in z.namelist() if n.endswith('/package/'+name)]
                    assert len(entries)==1 and z.read(entries[0],pwd=b'infected')==raw.encode()
        else:
            with tarfile.open(ROOT / archive,'r:gz') as t:
                for name,raw in files.items():
                    entries=[m for m in t.getmembers() if m.isfile() and m.name.removeprefix('./')=='package/'+name]
                    assert len(entries)==1 and t.extractfile(entries[0]).read()==raw.encode()
        ready.append({'pair':p,'snapshot':snapshot,'provenance':{'archive':archive,'sha256':a['sha256'],
                      'target_published':latest['target_published'],'dependency_published':latest['dependency_published'],
                      'constraint':latest['dependency']['after'],'files':{n:hashlib.sha256(v.encode()).hexdigest() for n,v in files.items()}},'prompt_tokens':tokens})
    except (ValueError,KeyError,FileNotFoundError,UnicodeError) as error:
        exclusions.append({'pair_id':p['id'],'dependency':a['name'],'version':a['version'],'reason':'source_or_context_unavailable','detail':str(error)})
selected = select_distinct(ready)
selected_keys={(r['pair']['id'],r['snapshot']['name']) for r in selected}
for row in ready:
    if (row['pair']['id'],row['snapshot']['name']) not in selected_keys:
        exclusions.append({'pair_id':row['pair']['id'],'dependency':row['snapshot']['name'],'version':row['snapshot']['version'],'reason':'shared_dependency_or_target_cap'})
assert len(selected)>=2
write(HERE/'pairs.jsonl',[r['pair'] for r in selected])
(HERE/'context-snapshots.json').write_text(json.dumps({r['pair']['id']:r['snapshot'] for r in selected},indent=2)+'\n')
write(HERE/'selection-audit.jsonl',[{k:v for k,v in r.items() if k not in ('pair','snapshot')} | {'pair_id':r['pair']['id'],'dependency':r['snapshot']['name'],'version':r['snapshot']['version']} for r in selected])
write(HERE/'selection-exclusions.jsonl',exclusions)
previous={r['id'] for r in read(ROOT/'data/evaluation/mixed-dev-20261002/pairs.jsonl')}
write(HERE/'dev-exclusions.jsonl',[{'pair_id':r['pair']['id'],'name':r['pair']['name'],'diff_sha256':r['pair']['diff_sha256'],
      'before':r['pair']['before'],'after':r['pair']['after'],'dependency':r['snapshot']['name'],
      'previous_D86_dev':r['pair']['id'] in previous,'MAL_historical_exposure':r['pair']['subset']=='MAL',
      'exclude_from_future_test_and_labeled_KB':True,'related_clone_exclusion_still_required':True} for r in selected])
report={'pool_pairs':len(pool),'available_semver_combinations':len(candidates),'selected':len(selected),'new_generations':2*len(selected),
        'cohorts':dict(Counter(r['pair']['subset'] for r in selected)), 'distinct_dependency_names':len({r['snapshot']['name'] for r in selected}),
        'exclusion_reasons':dict(Counter(r['reason'] for r in exclusions)), 'max_prompt_tokens':max(max(r['prompt_tokens'].values()) for r in selected),
        'human_gold_verified':False,'installed_versions_verified':False}
(HERE/'selection-summary.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
