"""Freeze the previously selected MAL extension of the D85 development experiment."""
import hashlib
import importlib.metadata
import json
import platform
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OLD = ROOT / 'data/evaluation/evidence-dev-20261001'
COHORT = ROOT / 'data/evaluation/mixed-dev-20261002'


def digest(path):
    hasher = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(8 * 1024**2), b''):
            hasher.update(chunk)
    return hasher.hexdigest()


def read(path):
    return [json.loads(line) for line in path.open()]


def write(name, rows):
    (HERE / name).write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows))


if (HERE / 'protocol.json').exists():
    raise SystemExit('Already frozen; refusing to overwrite')
selection = json.loads((COHORT / 'selection.json').read_text())
for name, expected in selection['artifact_sha256'].items():
    assert digest(COHORT / name) == expected, name
old_protocol = json.loads((OLD / 'protocol.json').read_text())
for name, expected in json.loads((OLD / 'artifact-manifest.json').read_text())['sha256'].items():
    assert digest(ROOT / name) == expected, name
for name in ('prompts.py', 'legacy_prompts.py', 'configs.py', 'evidence.py', 'run_batch.py'):
    shutil.copyfile(OLD / name, HERE / name)
sys.path.insert(0, str(HERE))
from prompts import ARMS, build
from transformers import AutoTokenizer

mixed = read(COHORT / 'pairs.jsonl')
pairs = [p for p in mixed if p['subset'] == 'MAL']
hn = [p for p in mixed if p['subset'] == 'HN']
assert len(pairs) == len(hn) == 32 and len({p['campaign'] for p in pairs}) == 32
assert {p['id']: p for p in hn} == {p['id']: p for p in read(OLD / 'pairs.jsonl')}
assert all(not p['truncated'] and p['annotation_status'] == 'pending' for p in pairs)
write('pairs.jsonl', pairs)
shutil.copyfile(OLD / 'pairs.jsonl', HERE / 'hn-historical-pairs.jsonl')
shutil.copyfile(OLD / 'results.jsonl', HERE / 'hn-historical-results.jsonl')
shutil.copyfile(COHORT / 'dev-exclusions.jsonl', HERE / 'dev-exclusions.jsonl')
model = old_protocol['model']
tokenizer = AutoTokenizer.from_pretrained(model['path'], local_files_only=True, trust_remote_code=False)
audits = []
for pair in pairs:
    for arm in ARMS[:-1]:
        messages = build(arm, pair)
        ids = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True)['input_ids']
        assert len(ids) + 2048 + 4096 < 32768, (pair['id'], arm, len(ids))
        audits.append({'pair_id': pair['id'], 'arm': arm, 'prompt_tokens': len(ids),
                       'prompt_messages_sha256': hashlib.sha256(json.dumps(messages).encode()).hexdigest()})
write('context-audit.jsonl', audits)
environment = {'python': platform.python_version(), 'platform': platform.platform(),
               'packages': {p: importlib.metadata.version(p) for p in
                            ('torch', 'vllm', 'transformers', 'tokenizers', 'jsonschema')}}
previous_env = json.loads((OLD / 'environment.json').read_text())
assert environment['packages'] == previous_env['packages'] and environment['python'] == previous_env['python']
(HERE / 'environment.json').write_text(json.dumps(environment, indent=2) + '\n')
shutil.copyfile(ROOT / 'docs/decisions.md', HERE / 'decisions-at-freeze.md')
shutil.copyfile(ROOT / 'docs/mixed-validation-20261011.md', HERE / 'protocol-description.md')
sources = list(HERE.glob('*.py')) + list(HERE.glob('*.jsonl'))
sources += [HERE / 'environment.json', HERE / 'decisions-at-freeze.md', HERE / 'protocol-description.md']
protocol = {'decision': 'D87', 'scope': 'exploratory_source_MAL_recall_and_unlabeled_HN_alarms',
            'model': model, 'arms': ARMS, 'pairs': 32, 'expected_generations': 160,
            'historical_hn_generations': 160, 'selection': 'All 32 MAL candidates frozen by D86; unchanged',
            'human_annotation_verified': False, 'label_origin': 'MAL upstream source label; HN unknown',
            'max_tokens': 2048, 'max_model_len': 32768, 'seed': 0, 'temperature': 0, 'top_p': 1,
            'kv_cache_memory_bytes': 6442450944,
            'source_sha256': {str(p.relative_to(ROOT)): digest(p) for p in sources},
            'upstream_sha256': {str(p.relative_to(ROOT)): digest(p) for p in
                               (COHORT / 'pairs.jsonl', COHORT / 'selection.json', OLD / 'protocol.json',
                                OLD / 'results.jsonl', OLD / 'pairs.jsonl')},
            'model_sha256': old_protocol['model_sha256'],
            'metrics': ['MAL source recall proxy with invalid-as-benign and sensitivity',
                        'HN alarm counts only; no FPR', 'paired transitions by cohort',
                        'JSON validity', 'citation existence and type', 'tokens and observed latency'],
            'not_claimed': ['human-gold accuracy', 'FPR improvement', 'RAG effect', 'confirmatory hypothesis test'],
            'interpretation': 'Previously exposed development data; HN control is historical, not a contemporaneous cohort.'}
for name, expected in protocol['model_sha256'].items():
    assert digest(Path(name)) == expected, name
(HERE / 'protocol.json').write_text(json.dumps(protocol, indent=2) + '\n')
print(json.dumps({'frozen': True, 'pairs': 32, 'new_generations': 160,
                  'historical_generations': 160, 'max_prompt_tokens': max(a['prompt_tokens'] for a in audits)}, indent=2))
