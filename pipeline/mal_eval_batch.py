"""Usage: python pipeline/mal_eval_batch.py --out DIR."""
import argparse
import fcntl
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    root = parser.parse_args().out
    manifest = json.loads((root / 'manifest.json').read_text())
    if manifest['errors'] or not manifest['models']:
        raise ValueError('Preparation is incomplete')
    with (root / '.batch.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        (root / 'batch.pid').write_text(str(os.getpid()) + '\n')
        states = {}
        def record(tag, stage, **fields):
            states[tag] = dict(stage=stage, time_utc=datetime.now(timezone.utc).isoformat(), **fields)
            temporary = root / 'batch-status.tmp.json'
            temporary.write_text(json.dumps(states, indent=2) + '\n')
            temporary.replace(root / 'batch-status.json')
            print(json.dumps(dict(model=tag, **states[tag])), flush=True)
        for tag in manifest['models']:
            out = root / tag
            try:
                record(tag, 'test_running')
                with (out / 'evaluation.log').open('a') as log:
                    subprocess.run([sys.executable, '-u', str(out / 'code/source_experiment.py'),
                                    '--release', str(out), '--stage', 'test'],
                                   stdout=log, stderr=subprocess.STDOUT, check=True)
                    record(tag, 'report_running')
                    subprocess.run([sys.executable, '-u', 'pipeline/mal_eval_report.py', '--release', str(out)],
                                   stdout=log, stderr=subprocess.STDOUT, check=True)
                record(tag, 'complete')
            except subprocess.CalledProcessError as error:
                record(tag, 'failed', error=str(error))
        complete = all(s['stage'] == 'complete' for s in states.values())
        (root / 'completion.json').write_text(json.dumps(dict(complete=complete, states=states,
                         excluded=manifest['excluded']), indent=2) + '\n')
        print(json.dumps(dict(batch_finished=True, complete=complete)), flush=True)
        if not complete:
            raise SystemExit(1)


if __name__ == '__main__':
    main()
