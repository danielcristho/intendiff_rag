"""Usage: python pipeline/extension_queue.py --out DIR --preparation-pid PID."""
import argparse
import fcntl
import json
import os
import sys
import time
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--preparation-pid', type=int, required=True)
    args = parser.parse_args()
    print('Waiting for preparation to exit before starting the additional-model batch.', flush=True)
    while True:
        try:
            os.kill(args.preparation_pid, 0)
        except ProcessLookupError:
            break
        time.sleep(5)
    errors = json.loads((args.out / 'preparation-errors.json').read_text())
    print(json.dumps(dict(preparation_errors=errors)), flush=True)
    # The first development run may have started while CPU audits were active.
    with (args.out / 'qwen25_7b/.run.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
    os.execv(sys.executable, [sys.executable, '-u', 'pipeline/extension_batch.py', '--out', str(args.out)])


if __name__ == '__main__':
    main()
