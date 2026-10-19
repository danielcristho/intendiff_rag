"""Freeze the two-version conditional dependency-context diagnostic."""
import hashlib
import importlib.metadata
import json
import platform
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OLD = ROOT / 'data/evaluation/mixed-validation-20261011'


def digest(path):
    hasher = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(8 * 1024**2), b''):
            hasher.update(chunk)
    return hasher.hexdigest()


if (HERE / 'protocol.json').exists():
    raise SystemExit('Already frozen')
for name in ('legacy_prompts.py', 'configs.py', 'evidence.py'):
    shutil.copyfile(OLD / name, HERE / name)
shutil.copyfile(OLD / 'prompts.py', HERE / 'base_prompts.py')
audit = json.loads((HERE / 'dependency-audit.json').read_text())
snapshots = {}
for v in audit['dependency_versions']:
    files = {}
    for name, record in v['files'].items():
        path = Path(record['path'])
        assert digest(path) == record['sha256']
        files[name] = path.read_text()
    snapshots['CTX-' + v['version']] = {'name': v['name'], 'version': v['version'], 'files': files}
(HERE / 'context-snapshots.json').write_text(json.dumps(snapshots, ensure_ascii=False, indent=2) + '\n')
old = json.loads((OLD / 'protocol.json').read_text())
sys.path.insert(0, str(HERE))
from prompts import ARMS, build
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained(old['model']['path'], local_files_only=True, trust_remote_code=False)
pairs = [json.loads(l) for l in (HERE / 'pairs.jsonl').open()]
assert len(pairs) == 20
context = []
for p in pairs:
    for arm in ARMS:
        ids = tokenizer.apply_chat_template(build(p, snapshots[arm]), tokenize=True, add_generation_prompt=True)['input_ids']
        assert len(ids) + 2048 <= 32768
        context.append({'pair_id': p['id'], 'arm': arm, 'prompt_tokens': len(ids)})
(HERE / 'context-audit.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in context))
shutil.copyfile(ROOT / 'docs/decisions.md', HERE / 'decisions-at-freeze.md')
shutil.copyfile(ROOT / 'docs/dependency-context-20261011.md', HERE / 'protocol-description.md')
env = {'python': platform.python_version(), 'platform': platform.platform(),
       'packages': {p: importlib.metadata.version(p) for p in ('torch','vllm','transformers','tokenizers','jsonschema')}}
previous = json.loads((OLD / 'environment.json').read_text())
assert env['python'] == previous['python'] and env['packages'] == previous['packages']
(HERE / 'environment.json').write_text(json.dumps(env, indent=2) + '\n')
files = list(HERE.glob('*.py')) + list(HERE.glob('*.jsonl')) + [HERE / x for x in
    ('dependency-audit.json', 'context-snapshots.json', 'decisions-at-freeze.md', 'protocol-description.md', 'environment.json')]
for source, destination in (
        ('pipeline/runner.py', 'retrieval-runner-at-freeze.txt'),
        ('tests/test_dependency_context.py', 'tests-at-freeze.txt'),
        ('scratchpad/dependency-context-20261011/audit.py', 'audit-at-freeze.txt'),
        ('scratchpad/dependency-context-20261011/semver-check.cjs', 'semver-at-freeze.txt')):
    shutil.copyfile(ROOT / source, HERE / destination)
    files.append(HERE / destination)
protocol = {'decision': 'D88', 'scope': 'post_hoc_conditional_dependency_version_diagnostic',
            'frozen_at_utc': datetime.now(timezone.utc).isoformat(),
            'model': old['model'], 'arms': ARMS, 'pairs': 20, 'expected_generations': 40,
            'max_tokens': 2048, 'max_model_len': 32768, 'kv_cache_memory_bytes': 6442450944,
            'seed': 0, 'temperature': 0, 'top_p': 1, 'human_annotation_verified': False,
            'actual_installed_version_verified': False, 'label_origin': 'Upstream target MAL; no dependency gold labels',
            'source_sha256': {str(p.relative_to(ROOT)): digest(p) for p in files},
            'upstream_sha256': {str(p.relative_to(ROOT)): digest(p) for p in
                (OLD / 'pairs.jsonl', OLD / 'results.jsonl', OLD / 'protocol.json')},
            'model_sha256': old['model_sha256']}
for name, expected in protocol['model_sha256'].items():
    assert digest(Path(name)) == expected
(HERE / 'protocol.json').write_text(json.dumps(protocol, indent=2) + '\n')
print(json.dumps({'frozen': True, 'new_generations': 40, 'max_prompt_tokens': max(r['prompt_tokens'] for r in context)}))
