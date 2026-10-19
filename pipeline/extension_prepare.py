"""Usage: python pipeline/extension_prepare.py --out DIR."""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

BASE = Path('data/evaluation/source-rag-v3-20261015')
MODELS = Path('data/evaluation/full-method-20261012/protocol.json')


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def pin(path):
    return dict(path=str(path), sha256=digest(path))


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise ValueError('Frozen adapter source differs from expected text')
    return text.replace(old, new, 1)


def additional_models():
    models = json.loads(MODELS.read_text())['models'][2:]
    for model in models:
        manifest = MODELS.parent / (model['tag'] + '.model-manifest.json')
        model['pins'] = json.loads(manifest.read_text())
        model['manifest_pin'] = pin(manifest)
        if not model['pins'] or not any(r['path'].endswith('.safetensors') for r in model['pins']):
            raise ValueError('Additional model lacks pinned weights')
    return models


def prepare(out, model, baseline):
    out.mkdir()
    code = out / 'code'
    code.mkdir()
    for path in (BASE / 'code').glob('*.py'):
        shutil.copyfile(path, code / path.name)
    shutil.copyfile('pipeline/extension_options.py', code / 'extension_options.py')
    for name in ('dev.pairs.jsonl', 'test.pairs.jsonl', 'kb.jsonl'):
        shutil.copyfile(BASE / name, out / name)
    (out / 'model.json').write_text(json.dumps(model, indent=2) + '\n')
    options = dict(model=model['id'], options={k: model[k] for k in ('chat_template_kwargs', 'stop_token_ids')})
    (out / 'model-options.json').write_text(json.dumps(options, indent=2) + '\n')
    runner = (code / 'runner.py').read_text()
    runner = replace_once(runner, 'from output_schema import RESPONSE_FORMAT',
                          'from extension_options import request_options\nfrom output_schema import RESPONSE_FORMAT')
    runner = replace_once(runner, '        **sampling,', '        **sampling,\n        **request_options(model),')
    (code / 'runner.py').write_text(runner)
    for row in model['pins']:
        if digest(row['path']) != row['sha256']:
            raise ValueError('Model pin changed: ' + row['path'])
    with (out / 'budget.log').open('w') as log:
        subprocess.run([sys.executable, '-u', 'pipeline/extension_audit.py', '--release', str(out)],
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    budget = json.loads((out / 'budget.json').read_text())
    model = dict(model, max_model_len=budget['max_model_len'], kv_cache_memory_bytes=budget['kv_cache_memory_bytes'])
    driver = (code / 'source_experiment.py').read_text()
    driver = replace_once(driver, "'--max-model-len', '32768'", "'--max-model-len', str(model['max_model_len'])")
    driver = replace_once(driver, "'--kv-cache-memory-bytes', '6442450944'", "'--kv-cache-memory-bytes', str(model['kv_cache_memory_bytes'])")
    (code / 'source_experiment.py').write_text(driver)
    pins = baseline['input_pins'] + [pin(BASE / 'protocol.json'), pin(MODELS), model['manifest_pin']]
    for path in sorted(out.rglob('*')):
        if path.is_file() and path.suffix != '.log' and '__pycache__' not in path.parts:
            pins.append(pin(path))
    pins += [pin(Path('pipeline') / name) for name in ('extension_prepare.py', 'extension_audit.py', 'extension_options.py')]
    protocol = dict(baseline, decision='D102', parent_release=str(BASE), models=[model], test_released=False,
                    dev_expected_generations=60, test_expected_generations=11406,
                    prepared_at_utc=datetime.now(timezone.utc).isoformat(), input_pins=pins,
                    evaluation_role='additional models selected after primary results were known')
    for name in ('protocol.json', 'protocol.dev.json'):
        (out / name).write_text(json.dumps(protocol, indent=2) + '\n')
    print(json.dumps(dict(model=model['tag'], prepared=True, max_model_len=model['max_model_len'],
                          kv_cache_memory_bytes=model['kv_cache_memory_bytes'])), flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    baseline = json.loads((BASE / 'protocol.json').read_text())
    if not baseline['test_released']:
        raise ValueError('Parent test release is not frozen')
    for row in baseline['input_pins']:
        if digest(row['path']) != row['sha256']:
            raise ValueError('Parent input pin changed: ' + row['path'])
    models = additional_models()
    manifest = dict(decision='D102', parent_release=str(BASE), models=[m['tag'] for m in models],
                    expected_test_generations=57030, expected_dev_generations=300)
    (args.out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    errors = []
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = {m['tag']: pool.submit(prepare, args.out / m['tag'], m, baseline) for m in models}
        for tag, future in futures.items():
            try:
                future.result()
            except Exception as error:
                errors.append(dict(model=tag, error=repr(error)))
    (args.out / 'preparation-errors.json').write_text(json.dumps(errors, indent=2) + '\n')
    print(json.dumps(dict(preparation_complete=True, errors=errors)), flush=True)


if __name__ == '__main__':
    main()
