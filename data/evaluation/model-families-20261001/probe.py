"""Download pinned tokenizer metadata and audit real prompts without inference."""
import hashlib
import json
from pathlib import Path

from huggingface_hub import HfApi, hf_hub_download, snapshot_download
from transformers import AutoTokenizer
from prompts import build

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
TARGETS = [('microsoft/Phi-4-mini-instruct', 'phi4_mini', 3.8, {}),
           ('meta-llama/Llama-3.1-8B-Instruct', 'llama31_8b', 8.0, {}),
           ('mistralai/Mistral-7B-Instruct-v0.3', 'mistral7b_v03', 7.0, {}),
           ('ibm-granite/granite-3.3-8b-instruct', 'granite33_8b', 8.0, {'thinking': False}),
           ('deepseek-ai/deepseek-coder-6.7b-instruct', 'deepseek67b', 6.7, {})]
pairs = list(map(json.loads, (HERE / 'pairs.jsonl').open()))
assert len(pairs) == 973
pins_path = HERE / 'candidate-pins.json'
pins = json.loads(pins_path.read_text()) if pins_path.exists() else []


def save(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    temporary.replace(path)


if not pins:
    for model_id, tag, nominal, kwargs in TARGETS:
        metadata = HfApi().model_info(model_id, files_metadata=True)
        pins.append({'id': model_id, 'tag': tag, 'revision': metadata.sha,
                     'path': str(ROOT / 'data/upstream/models' / tag),
                     'parameters_billion_nominal': nominal,
                     'parameters_billion': getattr(metadata.safetensors, 'total', 0) / 1e9 or nominal,
                     'chat_template_kwargs': kwargs, 'gated': metadata.gated,
                     'repository_files': [{'name': f.rfilename, 'size': f.size,
                         'sha256': f.lfs.sha256 if f.lfs else None} for f in metadata.siblings]})
    save(pins_path, pins)

reports = []
for model in pins:
    report = {k: model[k] for k in ['id', 'tag', 'revision', 'parameters_billion', 'gated']}
    try:
        hf_hub_download(model['id'], 'config.json', revision=model['revision'], local_dir=model['path'])
        filenames = [f['name'] for f in model['repository_files'] if '/' not in f['name'] and
                     (f['name'].endswith(('.json', '.txt', '.model', '.jinja', '.model.v3'))
                      or f['name'] in ['README.md', 'LICENSE', 'LICENSE-MODEL'])]
        snapshot_download(model['id'], revision=model['revision'], local_dir=model['path'],
                          allow_patterns=filenames, max_workers=4)
        config = json.loads((Path(model['path']) / 'config.json').read_text())
        tokenizer = AutoTokenizer.from_pretrained(model['path'], local_files_only=True,
                                                 trust_remote_code=False)
        audits = []
        for pair in pairs:
            for name in ['DIFF', 'DIFF+I']:
                messages = build(name, pair)
                assert messages == build(name, {**pair, 'label': 'hidden-label-audit'})
                encoded = tokenizer.apply_chat_template(messages, tokenize=True, return_dict=True,
                    add_generation_prompt=True, **model['chat_template_kwargs'])
                ids = encoded['input_ids']
                audits.append({'model': model['id'], 'revision': model['revision'],
                    'config': name, 'pair_id': pair['id'], 'prompt_tokens': len(ids),
                    'prompt_messages_sha256': hashlib.sha256(json.dumps(messages).encode()).hexdigest(),
                    'token_ids_sha256': hashlib.sha256(json.dumps(ids, separators=(',', ':')).encode()).hexdigest(),
                    'chat_template_kwargs': model['chat_template_kwargs']})
        native = config['max_position_embeddings']
        maximum = max(r['prompt_tokens'] for r in audits)
        required = maximum + 2048
        context = next((n for n in [32768, 49152] if required <= n <= native), None)
        selected_context = context or min(native, 49152)
        head_dim = config.get('head_dim', config['hidden_size'] // config['num_attention_heads'])
        kv_gib = 4 * config['num_hidden_layers'] * config.get('num_key_value_heads',
                   config['num_attention_heads']) * head_dim * selected_context / 2**30
        report.update({'accessible': True, 'audited_prompts': len(audits),
                       'architecture': config['architectures'], 'native_context': native,
                       'maximum_prompt_tokens': maximum, 'required_context': required,
                       'proposed_server_context': context,
                       'prompts_exceeding_native_context': sum(r['prompt_tokens']+2048>native for r in audits),
                       'weight_bf16_gib_estimate': model['parameters_billion']*1e9*2/2**30,
                       'kv_bf16_gib_at_proposed_context': kv_gib})
        (HERE / f'{model["tag"]}.candidate-audit.jsonl').write_text(
            ''.join(json.dumps(r) + '\n' for r in audits))
    except Exception as error:
        report.update({'accessible': False, 'failure_type': type(error).__name__})
    reports.append(report)
    save(HERE / 'candidate-audit.json', {'new_llm_calls': 0, 'candidates': reports})
    print(json.dumps(report), flush=True)
