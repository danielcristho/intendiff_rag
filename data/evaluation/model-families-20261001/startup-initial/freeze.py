"""Freeze the selected snapshots with python freeze.py before any inference."""
import hashlib
import importlib.metadata
import json
import platform
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = ROOT / 'data/evaluation/model-scale-20260930'
assert json.loads((HERE / 'download_status.json').read_text())['stage'] == 'complete'
assert not (HERE / 'protocol.json').exists() and not list(HERE.glob('*.results.jsonl'))
models = json.loads((HERE / 'models.json').read_text())
models = [{k: v for k, v in m.items() if k != 'repository_files'} for m in models]
audited, summaries = [], []
for model in models:
    selected = list(map(json.loads, (HERE / f'{model["tag"]}.candidate-audit.jsonl').open()))
    assert len(selected) == 1946 and model['max_model_len'] == 32768
    for row in selected:
        assert row['model'] == model['id'] and row['revision'] == model['revision']
        row['context_headroom_tokens'] = model['max_model_len'] - row['prompt_tokens'] - 2048
        assert row['context_headroom_tokens'] >= 0
    audited.extend(selected)
    summaries.append({'model': model['id'], 'prompts': len(selected),
        'max_prompt_tokens': max(r['prompt_tokens'] for r in selected),
        'minimum_context_headroom_tokens': min(r['context_headroom_tokens'] for r in selected)})
(HERE / 'context-audit.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in audited))
(HERE / 'context-audit.json').write_text(json.dumps({'verified': True, 'new_llm_calls': 0,
    'input_truncation_added': False, 'groups': summaries}, indent=2) + '\n')
software = {'python': platform.python_version(), 'platform': platform.platform(),
            'libraries': {n: importlib.metadata.version(n) for n in
                          ['vllm', 'torch', 'transformers', 'tokenizers', 'numpy', 'statsmodels']},
            'gpu': 'NVIDIA GeForce RTX 5090', 'gpu_total_mib': 32607, 'driver': '616.56',
            'gpu_used_during_preparation_mib': 2984,
            'inference_environment': {'VLLM_USE_FLASHINFER_SAMPLER': '0',
                'HF_HUB_OFFLINE': '1', 'TOKENIZERS_PARALLELISM': 'false'}}
(HERE / 'environment.json').write_text(json.dumps(software, indent=2) + '\n')
protocol = {'experiment_id': 'model-families-20261001', 'decision': 'D84',
    'scope': 'exploratory_source_labels', 'human_annotation_verified': False,
    'pair_count': 973, 'subsets': {'MAL': 873, 'TYP': 100}, 'models': models,
    'configs': ['DIFF', 'DIFF+I'], 'expected_runs': 3892, 'new_llm_calls': 3892,
    'historical_control': True, 'baseline_directory': str(BASE.relative_to(ROOT)),
    'historical_runs': 7784, 'combined_expected_runs': 11676,
    'seed': 0, 'temperature': 0., 'top_p': 1., 'max_tokens': 2048,
    'dtype': 'bfloat16', 'max_model_len': 32768, 'gpu_memory_utilization': .8,
    'max_num_seqs': 1, 'prefix_caching': True, 'generation_config': 'vllm',
    'warmup_requests': 0, 'tokenization_checks_per_model': 2,
    'invalid_policy': 'benign, with sensitivity treating invalid as malicious',
    'hypothesis_testing': False, 'retrieval_evaluation': False,
    'size_groups': {'A': '1<=P<5B total parameters', 'B': '5<=P<10B total parameters'},
    'pre_registered_outputs': ['MAL source recall proxy', 'TYP assumed-benign FPR',
        'JSON validity', 'invalid categories', 'invalid-as-malicious sensitivity',
        'campaign macro recall', 'paired transitions', 'tokens', 'observed session latency'],
    'limitations': ['Cross-family comparisons do not isolate parameter count or training.',
        'Historical Qwen3B/4B GPU allocation was 0.65; Qwen7B/8B and new models use 0.80.',
        'Phi and Llama requests explicitly include their native official end-of-turn token IDs.',
        'No human gold, HN, RAG, causal latency claim, formal temporal cutoff audit, or main-study tests.']}
names = ['probe.py', 'candidate-pins.json', 'candidate-audit.json', 'acquire.py', 'freeze.py',
    'server_check.py', 'preflight.py', 'evaluate.py', 'runner.py', 'runner.diff', 'prompts.py',
    'configs.py', 'analysis.py', 'summarize.py', 'reporting.py', 'compare.py', 'compare_report.py',
    'pairs.jsonl', 'kb.jsonl', 'models.json', 'context-audit.jsonl', 'context-audit.json', 'environment.json']
names.extend(f'{m["tag"]}.model-manifest.json' for m in models)
names.extend(f'{m["tag"]}.candidate-audit.jsonl' for m in models)
previous_names = ['pairs.jsonl', 'kb.jsonl', 'runner.py', 'prompts.py', 'configs.py', 'analysis.py',
    'results.all-models.jsonl', 'results.jsonl', 'comparison.json', 'summary.json',
    'protocol.json', 'environment.json', 'verification.json']
for field, directory, filenames in [('source_sha256', HERE, names), ('baseline_sha256', BASE, previous_names)]:
    protocol[field] = {str((directory / name).relative_to(ROOT)):
        hashlib.sha256((directory / name).read_bytes()).hexdigest() for name in filenames}
(HERE / 'protocol.json').write_text(json.dumps(protocol, indent=2) + '\n')
print(json.dumps({'frozen': True, 'new_runs': 3892, 'historical_runs': 7784,
                  'source_hashes': len(protocol['source_sha256'])}), flush=True)
