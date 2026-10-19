"""Verify frozen inputs and native end-of-turn request settings before inference."""
import ast
import hashlib
import importlib.metadata
import importlib.util
import json
import platform
from pathlib import Path
from unittest.mock import patch

from transformers import AutoTokenizer

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
protocol = json.loads((HERE / 'protocol.json').read_text())
baseline = ROOT / protocol['baseline_directory']
assert protocol['max_tokens'] == 2048 and protocol['expected_runs'] == 3892
assert protocol['historical_runs'] == 7784 and protocol['gpu_memory_utilization'] == .8
assert protocol['kv_cache_memory_bytes'] == 6 * 2**30
for field in ['source_sha256', 'baseline_sha256']:
    for name, expected in protocol[field].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, name
for model in protocol['models']:
    for entry in json.loads((HERE / f'{model["tag"]}.model-manifest.json').read_text()):
        with (ROOT / entry['path']).open('rb') as stream:
            assert hashlib.file_digest(stream, 'sha256').hexdigest() == entry['sha256']
    native = json.loads((Path(model['path']) / 'generation_config.json').read_text())['eos_token_id']
    assert model['stop_token_ids'] == native
    tokenizer = AutoTokenizer.from_pretrained(model['path'], local_files_only=True, trust_remote_code=False)
    # Transformers' all_special_ids omits some native added-token roles.
    serialized = json.loads((Path(model['path']) / 'tokenizer.json').read_text())
    special = {t['id']: t['content'] for t in serialized['added_tokens'] if t['special']}
    assert all(token in special for token in native)
    assert all(tokenizer.encode(special[token], add_special_tokens=False) == [token] for token in native)
for name in ['pairs.jsonl', 'prompts.py', 'configs.py', 'analysis.py', 'kb.jsonl']:
    assert (HERE / name).read_bytes() == (baseline / name).read_bytes(), name
environment = json.loads((baseline / 'environment.json').read_text())
assert platform.python_version() == environment['python']
assert all(importlib.metadata.version(n) == v for n, v in environment['libraries'].items())
previous = list(map(json.loads, (baseline / 'results.all-models.jsonl').open()))
assert len(previous) == len({r['run_key'] for r in previous}) == 7784
assert all(not r.get('error') and r['max_tokens'] == 2048 for r in previous)
audited = list(map(json.loads, (HERE / 'context-audit.jsonl').open()))
assert len(audited) == len({(r['model'], r['config'], r['pair_id']) for r in audited}) == 3892
assert min(r['context_headroom_tokens'] for r in audited) >= 0


def function_tree(path, name):
    node = next(n for n in ast.parse(path.read_text()).body
                if isinstance(n, ast.FunctionDef) and n.name == name)
    return ast.dump(node, include_attributes=False)


assert function_tree(HERE / 'runner.py', 'parse_verdict') == function_tree(baseline / 'runner.py', 'parse_verdict')
modules = []
for label, directory in [('historical_runner', baseline), ('new_runner', HERE)]:
    spec = importlib.util.spec_from_file_location(label, directory / 'runner.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    modules.append(module)


class Response:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return b'{"choices": [], "usage": {}}'


for model in protocol['models']:
    payloads = []
    for module in modules:
        with patch.object(module.urllib.request, 'urlopen', return_value=Response()) as mocked:
            module.call_llm('http://unused.invalid', model['id'],
                            [{'role': 'user', 'content': 'payload audit'}],
                            0, 180, {'temperature': 0., 'top_p': 1.})
        payloads.append(json.loads(mocked.call_args.args[0].data))
    assert payloads[1].pop('stop_token_ids') == model['stop_token_ids']
    assert payloads[1].pop('chat_template_kwargs') == model['chat_template_kwargs']
    assert payloads[0] == payloads[1], 'unexpected request field changed'
assert modules[0].run_key('m', 'DIFF', 'p', 0, 0.) != modules[1].run_key('m', 'DIFF', 'p', 0, 0.)
result = {'verified': True, 'historical_runs': len(previous), 'audited_prompts': len(audited),
          'minimum_context_headroom_tokens': min(r['context_headroom_tokens'] for r in audited),
          'model_files_sha256_verified': True, 'same_dependency_versions': True,
          'parser_unchanged': True, 'prompts_unchanged': True, 'network_requests_in_check': 0,
          'native_stop_tokens_verified': True, 'payload_diff_limited_to_native_model_options': True}
(HERE / 'preflight.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result), flush=True)
