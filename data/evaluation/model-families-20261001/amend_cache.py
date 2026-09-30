"""Record the zero-inference cache-allocation amendment with python amend_cache.py."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
assert not list(HERE.glob('*.results.jsonl')), 'inference must not have started'
initial = json.loads((HERE / 'protocol.initial.json').read_text())
assert json.loads((HERE / 'protocol.json').read_text()) == initial
for name, digest in initial['source_sha256'].items():
    archived = HERE / 'startup-initial' / Path(name).name
    assert hashlib.sha256(archived.read_bytes()).hexdigest() == digest
failure = (HERE / 'startup-initial/phi4_mini.server.log').read_text()
assert 'Tried to allocate 15.80 GiB' in failure and 'POST /v1/chat/completions' not in failure
amendment = {'at_utc': datetime.now(timezone.utc).isoformat(), 'new_inferences_before_change': 0,
    'reason': 'Phi startup failed while allocating a single automatic 15.80 GiB KV buffer.',
    'initial_protocol_sha256': hashlib.sha256((HERE / 'protocol.initial.json').read_bytes()).hexdigest(),
    'change': {'kv_cache_memory_bytes': 6 * 2**30, 'applies_to': [m['id'] for m in initial['models']]},
    'unchanged': ['weights', 'dtype', 'context length', 'prompt', 'parser', 'sampling', 'stop tokens', 'input'],
    'limitation': 'Explicit KV bytes overrides allocation inferred from gpu_memory_utilization; latency remains observational.',
    'root_cause': 'Large CUDA allocation failed; allocator/driver cause is not established.'}
(HERE / 'cache-amendment.json').write_text(json.dumps(amendment, indent=2) + '\n')
protocol = dict(initial)
protocol.update({'kv_cache_memory_bytes': 6 * 2**30, 'cache_allocation': 'explicit_bytes',
                 'gpu_memory_utilization_effective_for_cache': False, 'amendments': [amendment]})
protocol['limitations'] = initial['limitations'] + [amendment['limitation']]
paths = list(initial['source_sha256'])
paths.extend(str(p.relative_to(ROOT)) for p in [HERE / 'amend_cache.py', HERE / 'cache-amendment.json',
             HERE / 'protocol.initial.json'])
protocol['source_sha256'] = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in paths}
(HERE / 'protocol.json').write_text(json.dumps(protocol, indent=2) + '\n')
print(json.dumps({'amended_before_inference': True, 'kv_cache_bytes': 6 * 2**30,
                  'source_hashes': len(paths)}))
