"""Select a fresh development cohort and freeze all inputs before inference."""
import hashlib
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OLD = ROOT / 'data/evaluation/model-families-20261001'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return [json.loads(line) for line in path.open()]


def write(name, rows):
    (HERE / name).write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows))


if (HERE / 'protocol.json').exists():
    raise SystemExit('Already frozen; do not overwrite the protocol')
for src, dest in [(OLD / 'prompts.py', 'legacy_prompts.py'),
                  (OLD / 'configs.py', 'configs.py'),
                  (ROOT / 'pipeline/evidence.py', 'evidence.py')]:
    shutil.copyfile(src, HERE / dest)
sys.path.insert(0, str(HERE))
from prompts import ARMS, build
from transformers import AutoTokenizer

review = read(ROOT / 'data/review/pairs.jsonl')
historical = read(OLD / 'pairs.jsonl')
old_names = {r['name'] for r in historical}
old_hashes = {r['diff_sha256'] for r in historical}
old_trees = {r.get(k) for r in historical for k in ['sha256_before', 'sha256_after']}
eligible = [p for p in review if p['subset'] == 'HN' and not p['truncated']
            and p['diff_tokens'] <= 16000 and p['name'] not in old_names
            and p['diff_sha256'] not in old_hashes
            and not ({p.get('sha256_before'), p.get('sha256_after')} & old_trees)]
eligible.sort(key=lambda p: hashlib.sha256(('D85-dev|' + p['id']).encode()).hexdigest())
selected, names, hashes, trees = [], set(), set(), set()
for p in eligible:
    versions = {p.get('sha256_before'), p.get('sha256_after')}
    if p['name'] in names or p['diff_sha256'] in hashes or versions & trees:
        continue
    selected.append(p)
    names.add(p['name']); hashes.add(p['diff_sha256']); trees.update(versions)
    if len(selected) == 32:
        break
assert len(selected) == 32
write('pairs.jsonl', selected)
write('annotation-input.jsonl', selected)
write('dev-exclusions.jsonl', [{'id': p['id'], 'name': p['name'],
      'diff_sha256': p['diff_sha256'], 'sha256_before': p['sha256_before'],
      'sha256_after': p['sha256_after'], 'exclude_from': ['test', 'retrieval_kb'],
      'reason': 'D85 development exposure; related clones also require exclusion'} for p in selected])
model = json.loads((ROOT / 'data/evaluation/output-budget-20260929/protocol.json').read_text())['models'][1]
tokenizer = AutoTokenizer.from_pretrained(model['path'], local_files_only=True, trust_remote_code=False)
audits = []
for pair in selected:
    for arm in ARMS[:-1]:
        ids = tokenizer.apply_chat_template(build(arm, pair), tokenize=True, add_generation_prompt=True)['input_ids']
        assert len(ids) + 2048 + 4096 < 32768
        audits.append({'pair_id': pair['id'], 'arm': arm, 'prompt_tokens': len(ids),
                       'token_ids_sha256': hashlib.sha256(json.dumps(ids, separators=(',', ':')).encode()).hexdigest()})
write('context-audit.jsonl', audits)
sources = list(HERE.glob('*.py')) + list(HERE.glob('*.jsonl'))
sources += [ROOT / 'docs/decisions.md', ROOT / 'docs/evidence-dev-20261001.md']
protocol = {'decision': 'D85', 'scope': 'real_unlabeled_development_not_accuracy_evaluation',
            'model': model, 'arms': ARMS, 'pairs': 32, 'expected_generations': 160,
            'selection': 'SHA256 D85-dev|id; distinct package/diff/archive hashes; untruncated <=16000 prior tokens',
            'eligible_count': len(eligible), 'human_annotation_verified': False,
            'clustering_limit': 'HN clone/campaign mapping unavailable; package/hash separation is not campaign independence',
            'max_tokens': 2048, 'max_model_len': 32768, 'seed': 0,
            'temperature': 0, 'top_p': 1, 'kv_cache_memory_bytes': 6442450944,
            'source_sha256': {str(p.relative_to(ROOT)): digest(p) for p in sources},
            'upstream_sha256': {str(p.relative_to(ROOT)): digest(p) for p in
                [ROOT / 'data/review/pairs.jsonl', OLD / 'pairs.jsonl']},
            'model_sha256': {str(p): digest(p) for p in Path(model['path']).glob('*') if p.is_file()},
            'metrics': ['JSON validity', 'citation existence/type', 'verdict transitions', 'tokens', 'latency'],
            'not_measured': ['FPR', 'recall', 'semantic correctness', 'RAG benefit']}
(HERE / 'protocol.json').write_text(json.dumps(protocol, indent=2) + '\n')
print(json.dumps({'selected': len(selected), 'eligible': len(eligible),
                  'max_prompt_tokens': max(a['prompt_tokens'] for a in audits)}, indent=2))
