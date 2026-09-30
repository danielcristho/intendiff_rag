"""Verify frozen inputs, weight hashes, context limits, and request semantics."""
import ast
import hashlib
import importlib.metadata
import importlib.util
import json
import platform
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
protocol = json.loads((HERE / 'protocol.json').read_text())
baseline = ROOT / protocol['baseline_directory']
assert protocol['max_tokens'] == protocol['baseline_max_tokens'] == 2048
assert protocol['expected_runs'] == 3892 and protocol['gpu_memory_utilization'] == 0.8
for field in ['source_sha256', 'baseline_sha256']:
    for name, expected in protocol[field].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, name
for model in protocol['models']:
    for entry in json.loads((HERE / f'{model["tag"]}.model-manifest.json').read_text()):
        with (ROOT / entry['path']).open('rb') as stream:
            assert hashlib.file_digest(stream, 'sha256').hexdigest() == entry['sha256'], entry['path']
for name in ['pairs.jsonl', 'prompts.py', 'configs.py', 'analysis.py', 'kb.jsonl']:
    assert (HERE / name).read_bytes() == (baseline / name).read_bytes(), name
environment = json.loads((baseline / 'environment.json').read_text())
assert platform.python_version() == environment['python']
assert all(importlib.metadata.version(n) == v for n, v in environment['libraries'].items())
previous = list(map(json.loads, (baseline / 'results.jsonl').open()))
assert len(previous) == len({r['run_key'] for r in previous}) == 3892
assert all(not r.get('error') and r['max_tokens'] == 2048 for r in previous)
audited = list(map(json.loads, (HERE / 'context-audit.jsonl').open()))
assert len(audited) == len({(r['model'], r['config'], r['pair_id']) for r in audited}) == 3892
assert min(r['context_headroom_tokens'] for r in audited) >= 0


def tree(path, name):
    node = next(n for n in ast.parse(path.read_text()).body
                if isinstance(n, ast.FunctionDef) and n.name == name)
    return ast.dump(node, include_attributes=False)


assert tree(HERE / 'runner.py', 'parse_verdict') == tree(baseline / 'runner.py', 'parse_verdict')
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
                            0, 180, {'temperature': 0.0, 'top_p': 1.0})
        payloads.append(json.loads(mocked.call_args.args[0].data))
    if model['enable_thinking'] is False:
        assert payloads[1].pop('chat_template_kwargs') == {'enable_thinking': False}
    assert payloads[0] == payloads[1], 'unexpected request field changed'
assert modules[0].run_key('m', 'DIFF', 'p', 0, 0.0) != modules[1].run_key('m', 'DIFF', 'p', 0, 0.0)
result = {'verified': True, 'historical_runs': len(previous), 'audited_prompts': len(audited),
          'minimum_context_headroom_tokens': min(r['context_headroom_tokens'] for r in audited),
          'model_files_sha256_verified': True, 'same_dependency_versions': True,
          'parser_unchanged': True, 'prompts_unchanged': True, 'network_requests_in_check': 0,
          'qwen3_non_thinking_request_verified': True}
(HERE / 'preflight.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result), flush=True)
