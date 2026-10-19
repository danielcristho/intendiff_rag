"""Verify the frozen development preparation and record the CUDA blocker."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'data/evaluation/evidence-dev-20261001'
protocol = json.loads((HERE / 'protocol.json').read_text())
verified = {}
for section in ['source_sha256', 'upstream_sha256', 'model_sha256']:
    for name, expected in protocol[section].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, name
    verified[section] = len(protocol[section])
pairs = [json.loads(l) for l in (HERE / 'pairs.jsonl').open()]
excluded = [json.loads(l) for l in (HERE / 'dev-exclusions.jsonl').open()]
assert len(pairs) == len({p['id'] for p in pairs}) == 32
assert {p['id'] for p in pairs} == {p['id'] for p in excluded}
assert (HERE / 'pairs.jsonl').read_bytes() == (HERE / 'annotation-input.jsonl').read_bytes()
assert all(p['annotation_status'] == 'pending' for p in pairs)
context = [json.loads(l) for l in (HERE / 'context-audit.jsonl').open()]
assert len(context) == len({(r['pair_id'], r['arm']) for r in context}) == 128
assert all(r['prompt_tokens'] + 2048 + 4096 < 32768 for r in context)
results = HERE / 'results.jsonl'
assert not results.exists() or results.stat().st_size == 0
probe = json.loads((ROOT / 'scratchpad/fpr-audit-20261001/cuda-probe.json').read_text())
assert probe['checks']['driver_init_without_torch']['returncode'] == -11
assert probe['checks']['torch_init']['returncode'] == -11
assert probe['checks']['nvml']['returncode'] == 0
log = (HERE / 'server.log').read_text()
assert 'cuInit' in log and 'Segfault encountered' in log
assert 'POST /v1/chat/completions' not in log
record = {'preparation_verified': True, 'completed_inference': False,
          'actual_generations': 0, 'planned_generations': 160,
          'blocker': 'CUDA cuInit SIGSEGV on WSL; reproduced without torch; NVML works',
          'verified_hash_counts': verified, 'pairs': 32, 'audited_prompts': 128,
          'max_initial_prompt_tokens': max(r['prompt_tokens'] for r in context),
          'human_annotation_verified': False, 'accuracy_metrics_available': False}
(HERE / 'verification.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps(record, indent=2))
