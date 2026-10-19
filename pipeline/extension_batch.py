"""Usage: python pipeline/extension_batch.py --out DIR."""
import argparse
import fcntl
import hashlib
import json
import signal
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def freeze_driver_metadata(out):
    protocol = json.loads((out / 'protocol.json').read_text())
    if protocol.get('driver_metadata_frozen'):
        return
    if protocol['test_released'] or any(out.glob('*.results.jsonl')):
        raise ValueError('Cannot revise metadata after inference started')
    model, = protocol['models']
    protocol.update(max_model_len=model['max_model_len'],
                    kv_cache_memory_bytes=model['kv_cache_memory_bytes'], driver_metadata_frozen=True)
    for name in ('extension_batch.py', 'extension_release.py', 'extension_report.py'):
        path = Path(__file__).parent / name
        protocol['input_pins'].append(dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    for name in ('protocol.json', 'protocol.dev.json'):
        (out / name).write_text(json.dumps(protocol, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    root = args.out
    manifest = json.loads((root / 'manifest.json').read_text())
    status = {}
    def record(tag, stage, **fields):
        status[tag] = dict(stage=stage, time_utc=datetime.now(timezone.utc).isoformat(), **fields)
        temporary = root / 'batch-status.tmp.json'
        temporary.write_text(json.dumps(status, indent=2) + '\n')
        temporary.replace(root / 'batch-status.json')
        print(json.dumps(dict(model=tag, **status[tag])), flush=True)
    def run(tag, command):
        with (root / tag / 'evaluation.log').open('a') as log:
            subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True)
    with (root / '.batch.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        ready = []
        for tag in manifest['models']:
            out = root / tag
            if not (out / 'protocol.json').exists():
                record(tag, 'preparation_failed', error='See preparation-errors.json and budget.log')
                continue
            try:
                freeze_driver_metadata(out)
                record(tag, 'dev_running')
                run(tag, [sys.executable, '-u', str(out / 'code/source_experiment.py'), '--release', str(out), '--stage', 'dev'])
                run(tag, [sys.executable, '-u', 'pipeline/extension_release.py', '--release', str(out)])
                ready.append(tag)
                record(tag, 'test_ready')
            except subprocess.CalledProcessError as error:
                record(tag, 'dev_or_release_failed', error=str(error))
        for tag in ready:
            out = root / tag
            try:
                record(tag, 'test_running')
                run(tag, [sys.executable, '-u', str(out / 'code/source_experiment.py'), '--release', str(out), '--stage', 'test'])
                run(tag, [sys.executable, str(out / 'code/source_report.py'), '--release', str(out)])
                record(tag, 'complete', report=str(out / 'results.md'))
                subprocess.run([sys.executable, 'pipeline/extension_report.py', '--out', str(root)], check=True)
            except subprocess.CalledProcessError as error:
                record(tag, 'test_or_report_failed', error=str(error))
        subprocess.run([sys.executable, 'pipeline/extension_report.py', '--out', str(root)], check=True)
        print(json.dumps(dict(batch_finished=True, complete=all(r['stage'] == 'complete' for r in status.values()))), flush=True)


if __name__ == '__main__':
    def interrupted(signum, frame):
        raise KeyboardInterrupt(signum)
    signal.signal(signal.SIGTERM, interrupted)
    main()
