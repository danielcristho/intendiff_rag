"""Verify the frozen inputs and the single changed request field before inference."""
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
assert protocol['max_tokens'] == 2048 and protocol['baseline_max_tokens'] == 512
assert protocol['source_sha256'] and protocol['baseline_sha256']
for hashes in [protocol['source_sha256'], protocol['baseline_sha256']]:
    for name, expected in hashes.items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, name
for name in ['pairs.jsonl', 'prompts.py', 'configs.py', 'analysis.py', 'kb.jsonl']:
    assert (HERE / name).read_bytes() == (baseline / name).read_bytes(), name
environment = json.loads((baseline / 'environment.json').read_text())
assert platform.python_version() == environment['python']
assert all(importlib.metadata.version(name) == version for name, version in environment['libraries'].items())
rows = list(map(json.loads, (baseline / 'results.jsonl').open()))
assert len(rows) == len({r['run_key'] for r in rows}) == 3892
assert not any(r.get('error') for r in rows)
headroom = min(32768 - r['prompt_tokens'] - 2048 for r in rows)
assert headroom >= 0


def function_tree(path, name):
    module = ast.parse(path.read_text())
    node = next(n for n in module.body if isinstance(n, ast.FunctionDef) and n.name == name)
    return ast.dump(node, include_attributes=False)


assert function_tree(HERE / 'runner.py', 'parse_verdict') == function_tree(baseline / 'runner.py', 'parse_verdict')
modules = []
for label, directory in [('baseline_runner', baseline), ('candidate_runner', HERE)]:
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


payloads = []
for module in modules:
    with patch.object(module.urllib.request, 'urlopen', return_value=Response()) as mocked:
        module.call_llm('http://unused.invalid', 'model', [{'role': 'user', 'content': 'payload audit'}],
                        0, 180, {'temperature': 0.0, 'top_p': 1.0})
    payloads.append(json.loads(mocked.call_args.args[0].data))
assert payloads[0]['max_tokens'] == 512 and payloads[1]['max_tokens'] == 2048
payloads[1]['max_tokens'] = 512
assert payloads[0] == payloads[1], 'another request parameter changed'
assert modules[0].run_key('m', 'DIFF', 'p', 0, 0.0) != modules[1].run_key('m', 'DIFF', 'p', 0, 0.0)
result = {'verified': True, 'baseline_runs': len(rows), 'changed_request_fields': ['max_tokens'],
          'minimum_context_headroom_tokens': headroom, 'same_dependency_versions': True,
          'parser_unchanged': True, 'prompts_unchanged': True, 'network_requests_in_check': 0}
(HERE / 'preflight.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result), flush=True)
