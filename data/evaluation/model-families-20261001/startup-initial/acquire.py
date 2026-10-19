"""Download and hash the selected model snapshots using python acquire.py."""
import fcntl
import hashlib
import json
import time
from pathlib import Path

from huggingface_hub import snapshot_download

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
lock = (HERE / '.acquisition.lock').open('w')
fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
models = json.loads((HERE / 'models.json').read_text())


def save(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    temporary.replace(path)


def status(stage, **fields):
    record = {'stage': stage, 'updated_unix': time.time(), **fields}
    save(HERE / 'download_status.json', record)
    print(json.dumps(record), flush=True)


try:
    for model in models:
        status('downloading', model=model['id'], revision=model['revision'])
        allowed = [f['name'] for f in model['repository_files'] if '/' not in f['name'] and
                   (f['name'].endswith(('.json', '.safetensors', '.model', '.txt', '.jinja'))
                    or f['name'] in ['README.md', 'LICENSE', 'LICENSE-MODEL'])]
        snapshot_download(model['id'], revision=model['revision'], local_dir=model['path'],
                          allow_patterns=allowed, max_workers=4)
        manifest = []
        for entry in model['repository_files']:
            if entry['name'] not in allowed:
                continue
            path = Path(model['path']) / entry['name']
            assert path.is_file() and path.stat().st_size == entry['size'], entry['name']
            with path.open('rb') as stream:
                digest = hashlib.file_digest(stream, 'sha256').hexdigest()
            if entry['sha256']:
                assert digest == entry['sha256'], entry['name']
            manifest.append({'path': str(path.relative_to(ROOT)), 'bytes': path.stat().st_size,
                             'sha256': digest, 'upstream_lfs_sha256': entry['sha256']})
        assert any(f['path'].endswith('.safetensors') for f in manifest)
        save(HERE / f'{model["tag"]}.model-manifest.json', manifest)
        status('model_downloaded_and_verified', model=model['id'], files=len(manifest))
    status('complete', models=len(models))
except BaseException as error:
    status('error', error=str(error))
    raise
