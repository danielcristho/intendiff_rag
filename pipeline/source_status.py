"""Usage: python pipeline/source_status.py."""
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from samples import load_jsonl


def release_status(out):
    protocol = json.loads((out / 'protocol.json').read_text())
    print(f"test released   {protocol['test_released']}")
    for stage in ('dev', 'test'):
        expected = protocol[stage + '_expected_generations'] // len(protocol['models'])
        for model in protocol['models']:
            rows = load_jsonl(out / f'{stage}.{model["tag"]}.results.jsonl')
            completed = {r['run_key'] for r in rows if not r.get('error')}
            checked = out / f'{stage}.{model["tag"]}.verification.json'
            summary = json.loads(checked.read_text()) if checked.exists() else {}
            marker = 'verified' if summary.get('complete') and len(completed) == expected else '-'
            valid = summary.get('json_validity')
            suffix = f' JSON={valid:.1%}' if valid is not None and marker == 'verified' else ''
            if stage == 'dev' and valid is not None and marker == 'verified':
                suffix += ' gate=' + ('PASS' if valid >= protocol.get('dev_validity_threshold', 0.9) else 'FAIL')
            print(f"{stage:4} {model['tag']:14} {len(completed):5}/{expected:<5} {marker}{suffix}")
    status = out / 'status.json'
    if status.exists():
        record = json.loads(status.read_text())
        print('last stage:', record['stage'], record.get('model', ''), record.get('experiment_stage', ''))


def main():
    prep = Path('data/preparation/source-labelled-20261014')
    out = Path('data/evaluation/source-rag-v3-20261015')
    manifest = load_jsonl(prep / 'cohort/pairs.manifest.jsonl')
    normalized = {r['id']: r for r in load_jsonl(prep / 'cohort/pairs.preprocessed.jsonl')}
    exclusions = load_jsonl(prep / 'cohort/technical-exclusions.jsonl')
    print(f"normalization   {sum(not r.get('error') for r in normalized.values())}/{len(manifest)}")
    print(f"technical exclusions   {len(exclusions)}")
    release_status(out)
    extension = Path('data/evaluation/source-rag-extra-20261016')
    if (extension / 'manifest.json').exists():
        print('\nAdditional models D102:')
        manifest = json.loads((extension / 'manifest.json').read_text())
        batch = extension / 'batch-status.json'
        states = json.loads(batch.read_text()) if batch.exists() else {}
        print('Urutan: seluruh dev -> test model yang lolos (JSON dev >=90%).')
        print('verified = hasil sudah diperiksa; gate=FAIL = model belum boleh masuk test.')
        pid_file = extension / 'batch.pid'
        if pid_file.exists():
            pid = int(pid_file.read_text().strip())
            command_file = Path('/proc') / str(pid) / 'cmdline'
            command = command_file.read_bytes() if command_file.exists() else b''
            active = b'extension_batch.py' in command or b'extension_queue.py' in command
            print(f'batch process: {"running" if active else "not running"} (PID {pid})')
        for tag, state in states.items():
            if state['stage'].endswith('_running'):
                elapsed = max(0, int(time.time() - datetime.fromisoformat(state['time_utc']).timestamp()))
                print(f'active: {tag} {state["stage"]}, elapsed {elapsed // 60}m {elapsed % 60}s')
        for tag in manifest['models']:
            if (extension / tag / 'protocol.json').exists():
                print(tag, states.get(tag, {}).get('stage', 'prepared'))
                release_status(extension / tag)
            else:
                print(tag, states.get(tag, {}).get('stage', 'preparing'))
    supplement = Path('data/evaluation/source-rag-mal-20261018')
    if (supplement / 'manifest.json').exists():
        print('\nTambahan MAL D105:', flush=True)
        subprocess.run([sys.executable, 'pipeline/mal_eval_status.py', '--out', str(supplement)], check=True)


if __name__ == '__main__':
    main()
