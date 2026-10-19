"""Download the pinned official Granite snapshot and verify all weight hashes."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
from huggingface_hub import snapshot_download

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
os.environ['HF_HOME']=str(ROOT/'data/upstream/hf-cache')
model=json.loads((HERE/'model.json').read_text())
with (HERE/'.acquisition.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 allowed=[f['name'] for f in model['repository_files'] if '/' not in f['name'] and
          (f['name'].endswith(('.json','.safetensors','.txt','.model','.jinja')) or f['name'] in ('README.md','LICENSE'))]
 snapshot_download(model['id'],revision=model['revision'],local_dir=model['path'],allow_patterns=allowed,max_workers=4)
 manifest=[]
 for entry in model['repository_files']:
  if entry['name'] not in allowed:
   continue
  path=Path(model['path'])/entry['name']
  assert path.stat().st_size==entry['size'],entry['name']
  with path.open('rb') as stream:
   digest=hashlib.file_digest(stream,'sha256').hexdigest()
  if entry['sha256']:
   assert digest==entry['sha256'],entry['name']
  manifest.append({'path':str(path.relative_to(ROOT)),'sha256':digest,'bytes':path.stat().st_size,'upstream_lfs_sha256':entry['sha256']})
 assert sum(r['path'].endswith('.safetensors') for r in manifest)==4
 (HERE/'model-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print(json.dumps({'downloaded_and_verified':True,'model':model['id'],'revision':model['revision'],'files':len(manifest)}),flush=True)
