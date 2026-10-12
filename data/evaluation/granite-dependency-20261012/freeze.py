"""Freeze the new model comparison after download verification and before inference."""
import importlib.metadata
import json
import platform
import shutil
from datetime import datetime,timezone
from pathlib import Path
from selection import digest

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
OLD=ROOT/'data/evaluation/dependency-generalization-20261012'
assert not (HERE/'protocol.json').exists(),'Already frozen'
model=json.loads((HERE/'model.json').read_text())
manifest=json.loads((HERE/'model-manifest.json').read_text())
preflight=json.loads((HERE/'preflight.json').read_text())
assert 'OK' in (HERE/'tests.log').read_text()
for row in manifest:
    assert digest(ROOT/row['path'])==row['sha256']
env={'python':platform.python_version(),'platform':platform.platform(),
     'packages':{p:importlib.metadata.version(p) for p in ('torch','vllm','transformers','tokenizers','jsonschema')}}
previous=json.loads((OLD/'environment.json').read_text())
assert env['python']==previous['python'] and env['packages']==previous['packages']
(HERE/'environment.json').write_text(json.dumps(env,indent=2)+'\n')
old_manifest=json.loads((OLD/'artifact-manifest.json').read_text())['files']
for name in ('results.jsonl','protocol.json','pairs.jsonl','context-snapshots.json'):
    path=OLD/name
    assert digest(path)==old_manifest[str(path.relative_to(ROOT))]
for source,dest in [('docs/decisions.md','decisions-at-freeze.md'),('docs/granite-dependency-20261012.md','protocol-description.md'),
 ('tests/test_granite_dependency.py','tests-at-freeze.txt')]:
    shutil.copyfile(ROOT/source,HERE/dest)
shutil.copyfile(OLD/'results.jsonl',HERE/'qwen-historical-results.jsonl')
files=[p for p in HERE.iterdir() if p.is_file() and not p.name.startswith('.') and not p.name.startswith('download')]
upstream=[OLD/n for n in ('protocol.json','results.jsonl','artifact-manifest.json','pairs.jsonl','context-snapshots.json','dev-exclusions.jsonl')]
protocol={'decision':'D90','scope':'new_model_comparison_of_frozen_D89','frozen_at_utc':datetime.now(timezone.utc).isoformat(),
 'model':{k:v for k,v in model.items() if k!='repository_files'},'pairs':15,'expected_generations':30,'arms':['NO-SOURCE','WITH-SOURCE'],
 'max_tokens':2048,'max_model_len':preflight['max_model_len'],'kv_cache_memory_bytes':preflight['kv_cache_memory_bytes'],
 'seed':0,'temperature':0,'top_p':1,'chat_template_kwargs':{'thinking':False},'stop_token_ids':[0],
 'human_annotation_verified':False,'actual_installed_version_verified':False,
 'source_sha256':{str(p.relative_to(ROOT)):digest(p) for p in files},
 'upstream_sha256':{str(p.relative_to(ROOT)):digest(p) for p in upstream},
 'model_sha256':{r['path']:r['sha256'] for r in manifest}}
assert protocol['max_model_len']==32768 and protocol['kv_cache_memory_bytes']==6442450944
(HERE/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
print(json.dumps({'frozen':True,'expected_generations':30,'model':model['id'],'model_files':len(manifest),'source_files':len(files)}))
