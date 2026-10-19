"""Verify local model files against archived manifests before freezing a new run."""
import json
import os
from pathlib import Path

from common import HERE, ROOT, digest, write_json

HEX = set('0123456789abcdef')


# lfs_sha256 returns the digest a Hugging Face snapshot encodes in its blob link.
# Resolving the link fully was wrong: a newer cache layout adds a second hop into a
# content-addressed store whose filename is not the sha256 of the file.
def lfs_sha256(path):
    while path.is_symlink():
        target = Path(os.readlink(path))
        target = target if target.is_absolute() else path.parent / target
        if len(target.name) == 64 and set(target.name) <= HEX:
            return target.name
        path = target
    return None


assert not (HERE / 'protocol.json').exists()
models = json.loads((HERE / 'models.json').read_text())
known = {}
previous = json.loads((ROOT / 'data/evaluation/mixed-validation-20261011/protocol.json').read_text())
known.update({str((ROOT / path).resolve()): expected
              for path, expected in previous['model_sha256'].items()})
for path in (ROOT / 'data/evaluation').rglob('*model-manifest.json'):
    if path.parent == HERE:
        continue
    for row in json.loads(path.read_text()):
        if 'path' in row and 'sha256' in row:
            known[str((ROOT / row['path']).resolve())] = row['sha256']
for model in models:
    manifest = []
    for path in sorted(Path(model['path']).iterdir()):
        if not path.is_file():
            continue
        actual = digest(path)
        expected = known.get(str(path.resolve()))
        if path.suffix == '.safetensors':
            expected = lfs_sha256(path) or expected
        if expected is not None:
            assert actual == expected, str(path)
        assert path.suffix != '.safetensors' or expected is not None, 'Missing prior weight provenance'
        manifest.append({'path': str(path), 'bytes': path.stat().st_size, 'sha256': actual,
                         'historical_sha256_match': expected is not None})
    assert any(r['path'].endswith('.safetensors') for r in manifest)
    write_json(HERE / f"{model['tag']}.model-manifest.json", manifest)
    print(json.dumps({'model': model['id'], 'pinned_files': len(manifest)}), flush=True)
