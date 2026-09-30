"""Audit local tokenizers and freeze the protocol before any new inference."""
import hashlib
import importlib.metadata
import json
import os
import platform
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = ROOT / 'data/evaluation/output-budget-20260929'
assert json.loads((HERE / 'download_status.json').read_text())['stage'] == 'complete'
assert not (HERE / 'protocol.json').exists(), 'the protocol is already frozen'
assert not list(HERE.glob('*.results.jsonl')), 'inference already exists'
environment = dict(os.environ, HF_HUB_OFFLINE='1', TOKENIZERS_PARALLELISM='false')
subprocess.run([sys.executable, str(HERE / 'context_audit.py')], cwd=ROOT,
               env=environment, check=True)
models = json.loads((HERE / 'models.json').read_text())
comparators = {'qwen25_7b': 'Qwen/Qwen2.5-Coder-3B-Instruct',
               'qwen3_8b': 'Qwen/Qwen3-4B-Instruct-2507'}
models = [{**{k: v for k, v in m.items() if k != 'repository_files'},
           'comparison_model': comparators[m['tag']]} for m in models]
software = {'python': platform.python_version(), 'platform': platform.platform(),
            'libraries': {n: importlib.metadata.version(n) for n in
                          ['vllm', 'torch', 'transformers', 'tokenizers', 'numpy', 'statsmodels']},
            'gpu': 'NVIDIA GeForce RTX 5090', 'gpu_total_mib': 32607, 'driver': '616.56',
            'gpu_used_before_download_mib': 3145,
            'inference_environment': {'VLLM_USE_FLASHINFER_SAMPLER': '0',
                                      'HF_HUB_OFFLINE': '1', 'TOKENIZERS_PARALLELISM': 'false'}}
(HERE / 'environment.json').write_text(json.dumps(software, indent=2) + '\n')
protocol = {'experiment_id': 'model-scale-20260930', 'decision': 'D83',
            'scope': 'exploratory_source_labels', 'human_annotation_verified': False,
            'pair_count': 973, 'subsets': {'MAL': 873, 'TYP': 100}, 'models': models,
            'configs': ['DIFF', 'DIFF+I'], 'expected_runs': 3892, 'new_llm_calls': 3892,
            'historical_control': True, 'baseline_directory': str(BASE.relative_to(ROOT)),
            'historical_runs': 3892, 'combined_expected_runs': 7784,
            'seed': 0, 'temperature': 0.0, 'top_p': 1.0, 'max_tokens': 2048,
            'baseline_max_tokens': 2048, 'dtype': 'bfloat16', 'max_model_len': 32768,
            'gpu_memory_utilization': 0.8, 'baseline_gpu_memory_utilization': 0.65,
            'max_num_seqs': 1, 'prefix_caching': True, 'warmup_requests': 0,
            'tokenization_checks_per_model': 2,
            'invalid_policy': 'benign, with sensitivity treating invalid as malicious',
            'hypothesis_testing': False, 'retrieval_evaluation': False,
            'size_groups': {'A': '1<=P<5B total parameters', 'B': '5<=P<10B total parameters'},
            'pre_registered_outputs': ['MAL source recall proxy', 'TYP assumed-benign FPR',
                'JSON validity', 'invalid categories', 'invalid-as-malicious sensitivity',
                'campaign macro recall', 'paired transitions', 'tokens', 'observed session latency'],
            'limitations': ['Qwen3 checkpoints differ in post-training as well as parameter count.',
                'Historical controls used GPU allocation 0.65; larger models use 0.80.',
                'No human gold, HN, RAG, causal latency claim, or main-study hypothesis tests.',
                'Model release cutoffs for formal temporal analysis are not established in this experiment.']}
source_names = ['acquire.py', 'freeze.py', 'context_audit.py', 'server_check.py', 'preflight.py',
                'evaluate.py', 'runner.py', 'runner.diff', 'prompts.py', 'configs.py', 'analysis.py',
                'summarize.py', 'reporting.py', 'compare.py', 'pairs.jsonl', 'kb.jsonl',
                'models.json', 'context-audit.jsonl', 'context-audit.json', 'environment.json']
source_names.extend(f'{m["tag"]}.model-manifest.json' for m in models)
baseline_names = ['pairs.jsonl', 'kb.jsonl', 'runner.py', 'prompts.py', 'configs.py', 'analysis.py',
                  'results.jsonl', 'qwen25.results.jsonl', 'qwen3.results.jsonl', 'summary.json',
                  'protocol.json', 'environment.json', 'verification.json']
for field, directory, names in [('source_sha256', HERE, source_names),
                                ('baseline_sha256', BASE, baseline_names)]:
    protocol[field] = {str((directory / name).relative_to(ROOT)):
                       hashlib.sha256((directory / name).read_bytes()).hexdigest() for name in names}
(HERE / 'protocol.json').write_text(json.dumps(protocol, indent=2) + '\n')
print(json.dumps({'frozen': True, 'new_runs': 3892, 'historical_runs': 3892,
                  'source_hashes': len(protocol['source_sha256'])}), flush=True)
