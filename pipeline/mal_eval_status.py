"""Usage: python pipeline/mal_eval_status.py --out DIR."""
import argparse
import json
from pathlib import Path


def read_json(path, default):
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    root = parser.parse_args().out
    manifest = read_json(root / 'manifest.json', {})
    states = read_json(root / 'batch-status.json', {})
    pid_path = root / 'batch.pid'
    active = False
    if pid_path.exists():
        command = Path('/proc') / pid_path.read_text().strip() / 'cmdline'
        active = command.exists() and b'mal_eval_batch.py' in command.read_bytes()
    print('MAL tambahan: 96 pair / 65 kampanye; 6 konfigurasi per model.')
    print('Batch:', 'running' if active else 'not running')
    for tag in manifest.get('models', []):
        out = root / tag
        results = out / f'test.{tag}.results.jsonl'
        completed, errors = set(), 0
        if results.exists():
            for line in results.read_text().splitlines():
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if row.get('error'):
                    errors += 1
                else:
                    completed.add(row['run_key'])
        checked = read_json(out / f'test.{tag}.verification.json', {})
        verified = checked.get('complete') and len(completed) == 576
        state = states.get(tag, {}).get('stage', 'queued')
        print(f'{tag:14} {len(completed):3}/576 {state} '
              f'{"verified" if verified else ""} transport_errors={errors}')
        if state == 'test_running':
            current = read_json(out / 'status.json', {})
            print('  stage:', current.get('stage', 'checking pins/dev'))
    for row in manifest.get('excluded', []):
        print(row['tag'], 'EXCLUDED:', row['reason'], f"JSON={row['dev_json_validity']:.1%}")
    for row in manifest.get('errors', []):
        print('PREPARATION ERROR:', row)
    completion = read_json(root / 'completion.json', {})
    if completion:
        print('All eligible models complete:', completion['complete'])


if __name__ == '__main__':
    main()
