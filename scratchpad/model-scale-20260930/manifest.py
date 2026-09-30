"""Freeze checksums of the completed exploratory artifacts and report."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'data/evaluation/model-scale-20260930'
assert json.loads((HERE / 'status.json').read_text())['stage'] == 'complete'
assert json.loads((HERE / 'verification.json').read_text())['verified']
files = [p for p in HERE.iterdir() if p.is_file() and not p.name.startswith('.')
         and p.name != 'artifact-manifest.json']
files.extend((ROOT / 'scratchpad/model-scale-20260930').glob('*.py'))
files.extend(ROOT / p for p in ['docs/model-scale-20260930.md',
              'docs/model-scale-proposal-20260930.md', 'docs/decisions.md',
              'README.md', '.agent/experiments.md'])
entries = []
for path in sorted(files):
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    entries.append({'path': str(path.relative_to(ROOT)), 'bytes': path.stat().st_size,
                    'sha256': digest})
manifest = {'experiment_id': 'model-scale-20260930', 'complete': True,
            'generated_at_utc': datetime.now(timezone.utc).isoformat(),
            'new_runs': 3892, 'historical_runs': 3892,
            'note': 'Document checksums describe this snapshot; future decision log additions are separate history.',
            'files': entries}
(HERE / 'artifact-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
for entry in entries:
    with (ROOT / entry['path']).open('rb') as stream:
        assert hashlib.file_digest(stream, 'sha256').hexdigest() == entry['sha256']
print(json.dumps({'verified_manifest_files': len(entries)}))
