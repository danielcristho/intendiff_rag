"""Freeze the entire updated-method matrix before any new generation."""
import importlib.metadata
import json
import platform
import shutil
from datetime import datetime, timezone

from transformers import AutoTokenizer
from common import ARMS, HERE, ROOT, digest, read_rows, write_json

assert not (HERE / 'protocol.json').exists(), 'Already frozen'
assert 'OK' in (HERE / 'tests.log').read_text()
summary = json.loads((HERE / 'input-summary.json').read_text())
models = json.loads((HERE / 'models.json').read_text())
pairs = read_rows(HERE / 'pairs.jsonl')
originals = read_rows(HERE / 'original-pairs.jsonl')
historical = json.loads((ROOT / 'data/evaluation/model-families-20261001/protocol.json').read_text())
assert digest(HERE / 'original-pairs.jsonl') == historical['source_sha256'][
    'data/evaluation/model-families-20261001/pairs.jsonl']
assert [p['id'] for p in pairs] == [p['id'] for p in originals] and len(pairs) == 973
assert summary['models'] == len(models) == 7 and summary['dropped_pairs'] == 0
budget = {r['pair_id']: r for r in read_rows(HERE / 'input-budget.jsonl')}
token_audit = read_rows(HERE / 'token-audit.jsonl')
assert len(token_audit) == len({(r['pair_id'], r['model_tag'], r['arm']) for r in token_audit}) == 13622
assert max(r['prompt_tokens'] for r in token_audit) <= 26624
base_model = next(m for m in models if m['tag'] == 'qwen25')
tokenizer = AutoTokenizer.from_pretrained(base_model['path'], local_files_only=True, trust_remote_code=False)
for pair, original in zip(pairs, originals):
    change = budget[pair['id']]
    assert pair['diff'].splitlines() == original['diff'].splitlines()[:change['kept_lines']]
    assert all(pair[k] == original[k] for k in original if k not in ('diff', 'diff_sha256', 'truncated'))
    # Keep the original token count explicitly instead of labelling it as the trimmed count.
    pair['source_diff_tokens'] = pair['diff_tokens']
    pair['diff_tokens'] = len(tokenizer.encode(pair['diff'], add_special_tokens=False))
(HERE / 'pairs.jsonl').write_text(''.join(json.dumps(p, ensure_ascii=False) + '\n' for p in pairs))
for model in models:
    manifest = json.loads((HERE / f"{model['tag']}.model-manifest.json").read_text())
    assert all(r['historical_sha256_match'] for r in manifest if r['path'].endswith('.safetensors'))
for name in ('prompts.py', 'legacy_prompts.py', 'configs.py', 'evidence.py'):
    assert (HERE / name).read_bytes() == (ROOT / 'data/evaluation/mixed-validation-20261011' / name).read_bytes()
for source, destination in [('docs/full-method-20261012.md', 'protocol-description.md'),
    ('docs/decisions.md', 'decisions-at-freeze.md'), ('tests/test_full_method.py', 'tests-at-freeze.txt')]:
    shutil.copyfile(ROOT / source, HERE / destination)
write_json(HERE / 'environment.json', {'python': platform.python_version(),
    'packages': {p: importlib.metadata.version(p) for p in ('torch', 'vllm', 'transformers', 'tokenizers', 'jsonschema')}})
files = [p for p in HERE.iterdir() if p.is_file() and not p.name.startswith('.') and p.suffix != '.log']
protocol = {'decision': 'D92', 'experiment_id': HERE.name,
    'frozen_at_utc': datetime.now(timezone.utc).isoformat(),
    'scope': 'complete source-labelled cohort with ID-diff, schema and verifier',
    'models': models, 'arms': ARMS, 'pair_count': 973, 'expected_new_generations': 20433,
    'historical_generations_used_as_new_results': 0, 'seed': 0, 'temperature': 0, 'top_p': 1,
    'max_tokens': 2048, 'max_model_len': 32768, 'kv_cache_memory_bytes': 6442450944,
    'human_annotation_verified': False, 'retrieval_evaluation': False,
    'dependency_context_included': False, 'warmup_generations': 0, 'automatic_retries': 0,
    'input_budget_summary': summary,
    'source_sha256': {str(p.relative_to(ROOT)): digest(p) for p in files}}
write_json(HERE / 'protocol.json', protocol)
print(json.dumps({'frozen': True, 'pairs': 973, 'models': 7, 'new_generations': 20433}), flush=True)
