"""Rebuild intent from local predecessor files; inspect frozen artifact hashes."""
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

from transformers import AutoTokenizer

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'pipeline'))
from intent import build

folders = ['source-baselines-20260929', 'output-budget-20260929',
           'model-scale-20260930', 'model-families-20261001', 'evidence-dev-20261001']
hashes = []
for folder in folders:
    path = ROOT / 'data/evaluation' / folder / 'artifact-manifest.json'
    if not path.exists():
        hashes.append({'manifest': str(path.relative_to(ROOT)), 'missing': True})
        continue
    manifest = json.loads(path.read_text())
    files = manifest.get('sha256') or {r['path']: r['sha256'] for r in manifest['files']}
    mismatches = []
    for name, expected in files.items():
        target = ROOT / name
        actual = hashlib.sha256(target.read_bytes()).hexdigest() if target.exists() else None
        if actual != expected:
            mismatches.append({'path': name, 'expected': expected, 'actual': actual,
                               'experiment_artifact': name.startswith('data/evaluation/')})
    hashes.append({'manifest': str(path.relative_to(ROOT)), 'files': len(files), 'mismatches': mismatches})
    assert not any(m['experiment_artifact'] for m in mismatches), mismatches
protocol = json.loads((ROOT / 'data/evaluation/output-budget-20260929/protocol.json').read_text())
tokenizer = AutoTokenizer.from_pretrained(protocol['models'][0]['path'], local_files_only=True, trust_remote_code=False)
count = lambda text: len(tokenizer(text)['input_ids'])
pairs = [json.loads(l) for l in (ROOT / 'data/evaluation/model-families-20261001/pairs.jsonl').open()]
pairs += [json.loads(l) for l in (ROOT / 'data/evaluation/evidence-dev-20261001/pairs.jsonl').open()]
issues, matched, manifest_versions, version_differences = [], 0, Counter(), []
for pair in pairs:
    before = ROOT / pair['before_dir']
    if not before.is_dir():
        issues.append({'pair_id': pair['id'], 'issue': 'missing_predecessor_directory'})
        continue
    rebuilt = build(before, count)
    if rebuilt != pair['intent']:
        issues.append({'pair_id': pair['id'], 'issue': 'intent_rebuild_mismatch',
                       'fields': [k for k in rebuilt if rebuilt[k] != pair['intent'].get(k)]})
    else:
        matched += 1
    manifest = before / 'package.json'
    if manifest.exists():
        try:
            version = json.loads(manifest.read_text()).get('version')
            manifest_versions['matches' if version == pair['before'] else 'differs_or_absent'] += 1
            if version != pair['before']:
                version_differences.append({'pair_id': pair['id'], 'recorded_before': pair['before'],
                    'manifest_version': version,
                    'only_plus_suffix': isinstance(version, str) and version.split('+', 1)[0] == pair['before']})
        except (UnicodeError, ValueError):
            manifest_versions['unparseable'] += 1
report = {'pairs_checked': len(pairs), 'intent_exact_rebuilds': matched, 'issues': issues,
          'predecessor_manifest_versions': manifest_versions, 'artifact_manifests': hashes,
          'version_differences': version_differences,
          'intent_builder_sha256': hashlib.sha256((ROOT / 'pipeline/intent.py').read_bytes()).hexdigest(),
          'qualification': 'Exact match to predecessor-derived input does not verify its claims or human gold labels.'}
(OUT / 'input-audit.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
