"""Freeze the selected cohort, model, source and provenance before inference."""
import importlib.metadata
import json
import platform
import shutil
from datetime import datetime,timezone
from pathlib import Path
from selection import digest

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
assert not (HERE/'protocol.json').exists(),'Already frozen'
old=json.loads((ROOT/'data/evaluation/dependency-context-20261011/protocol.json').read_text())
summary=json.loads((HERE/'selection-summary.json').read_text())
env={'python':platform.python_version(),'platform':platform.platform(),
     'packages':{p:importlib.metadata.version(p) for p in ('torch','vllm','transformers','tokenizers','jsonschema')}}
previous=json.loads((ROOT/'data/evaluation/dependency-context-20261011/environment.json').read_text())
assert env['python']==previous['python'] and env['packages']==previous['packages']
(HERE/'environment.json').write_text(json.dumps(env,indent=2)+'\n')
for source,dest in [('docs/decisions.md','decisions-at-freeze.md'),
 ('docs/dependency-generalization-20261012.md','protocol-description.md'),
 ('tests/test_dependency_generalization.py','tests-at-freeze.txt'),
 ('scratchpad/dependency-generalization-20261012/fetch_times.py','fetch-times-at-freeze.txt'),
 ('scratchpad/dependency-context-20261011/semver-check.cjs','semver-at-freeze.txt')]:
    shutil.copyfile(ROOT/source,HERE/dest)
files=[p for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts and not p.name.startswith('.')]
upstream=[ROOT/p for p in ('data/acquisition/pairs.preprocessed-v2.jsonl','data/acquisition/extracted.typical.jsonl',
 'data/acquisition/datadog.inventory-full.jsonl','data/acquisition/samples.typical.jsonl',
 'data/evaluation/dependency-context-20261011/protocol.json','data/evaluation/mixed-dev-20261002/pairs.jsonl')]
for row in [json.loads(x) for x in (HERE/'selection-audit.jsonl').read_text().splitlines()]:
    path=ROOT/row['provenance']['archive']
    assert digest(path)==row['provenance']['sha256']
    upstream.append(path)
protocol={'decision':'D89','scope':'conditional_dependency_source_availability_diagnostic',
          'frozen_at_utc':datetime.now(timezone.utc).isoformat(),'model':old['model'],
          'pairs':summary['selected'],'expected_generations':summary['new_generations'],'arms':['NO-SOURCE','WITH-SOURCE'],
          'max_tokens':2048,'max_model_len':32768,'kv_cache_memory_bytes':6442450944,'temperature':0,'seed':0,'top_p':1,
          'human_annotation_verified':False,'actual_installed_version_verified':False,
          'source_sha256':{str(p.relative_to(ROOT)):digest(p) for p in files},
          'upstream_sha256':{str(p.relative_to(ROOT)):digest(p) for p in upstream},'model_sha256':old['model_sha256']}
for name,expected in protocol['model_sha256'].items():
    assert digest(Path(name))==expected
(HERE/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
print(json.dumps({'frozen':True,'pairs':summary['selected'],'generations':summary['new_generations'],'source_pins':len(files)}))
