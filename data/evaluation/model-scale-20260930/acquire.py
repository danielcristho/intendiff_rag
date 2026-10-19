"""Pin and download the two selected official model repositories."""
import argparse
import fcntl
import hashlib
import json
import time
from pathlib import Path

from huggingface_hub import HfApi, snapshot_download

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
TARGETS = [('Qwen/Qwen2.5-Coder-7B-Instruct', 'qwen25_7b', 'qwen2.5-coder-7b-instruct', 7.61),
           ('Qwen/Qwen3-8B', 'qwen3_8b', 'qwen3-8b', 8.2)]
parser = argparse.ArgumentParser()
parser.add_argument('--metadata-only', action='store_true')
args = parser.parse_args()
lock = (HERE / '.acquisition.lock').open('w')
fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)


def write(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    temporary.replace(path)


def status(stage, **fields):
    record = {'stage': stage, 'updated_unix': time.time(), **fields}
    write(HERE / 'download_status.json', record)
    print(json.dumps(record), flush=True)


try:
    pinned_path = HERE / 'models.json'
    if pinned_path.exists():
        models = json.loads(pinned_path.read_text())
        assert [m['id'] for m in models] == [t[0] for t in TARGETS]
    else:
        models = []
        for model_id, tag, directory, parameters in TARGETS:
            info = HfApi().model_info(model_id, files_metadata=True)
            files = [{'name': f.rfilename, 'size': f.size,
                      'sha256': f.lfs.sha256 if f.lfs else None} for f in info.siblings]
            models.append({'id': model_id, 'tag': tag, 'revision': info.sha,
                           'path': str(ROOT / 'data/upstream/models' / directory),
                           'parameters_billion': parameters, 'size_group': 'B: 5<=P<10B',
                           'enable_thinking': False if tag == 'qwen3_8b' else None,
                           'repository_files': files})
            status('revision_pinned', model=model_id, revision=info.sha)
        write(pinned_path, models)
    if not args.metadata_only:
        for model in models:
            status('downloading', model=model['id'], revision=model['revision'])
            snapshot_download(model['id'], revision=model['revision'], local_dir=model['path'],
                              allow_patterns=['*.json', '*.safetensors', '*.model', '*.txt',
                                              '*.jinja', 'README.md', 'LICENSE*'], max_workers=4)
            manifest = []
            for entry in model['repository_files']:
                path = Path(model['path']) / entry['name']
                if not path.is_file():
                    continue
                with path.open('rb') as stream:
                    digest = hashlib.file_digest(stream, 'sha256').hexdigest()
                if entry['sha256']:
                    assert digest == entry['sha256'], str(path)
                manifest.append({'path': str(path.relative_to(ROOT)), 'bytes': path.stat().st_size,
                                 'sha256': digest, 'upstream_lfs_sha256': entry['sha256']})
            assert any(f['path'].endswith('.safetensors') for f in manifest)
            write(HERE / f'{model["tag"]}.model-manifest.json', manifest)
            status('model_downloaded_and_verified', model=model['id'], files=len(manifest))
    status('metadata_complete' if args.metadata_only else 'complete', models=len(models))
except BaseException as error:
    status('error', error=str(error))
    raise
