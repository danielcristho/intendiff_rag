"""Usage: python pipeline/sampling_batch.py --release DIR (resumable; verified cells are skipped)."""
import argparse
import fcntl
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

from sampling_grid import cells, stem
from source_experiment import SERVER_ENV, check_pins, served, warm_up
from source_results import verify

RUNTIME_PROBE = 'import importlib.metadata as m, json, sys; print(json.dumps({p: m.version(p) for p in sys.argv[1:]}))'


def check_runtime(protocol):
    # Greedy output already moved between GPU and vLLM builds (D54); a new
    # runtime would confound the decoding effect with the environment.
    pinned = protocol['runtime']['packages']
    # absolute(), not resolve(): resolving follows the venv symlink to the bare interpreter.
    probe = subprocess.run([str(Path('.venv/bin/python').absolute()), '-c', RUNTIME_PROBE, *pinned],
                           capture_output=True, text=True, check=True)
    found = json.loads(probe.stdout)
    if found != pinned:
        raise RuntimeError(f'Runtime differs from the T=0 run: {found} != {pinned}')


def grid(protocol):
    return cells(protocol['temperatures'], protocol['seeds'])


def verify_cell(release, model, temperature, seed):
    return verify(release, 'test', model, seed, temperature, stem(model['tag'], temperature, seed))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--release', type=Path, required=True)
    release = parser.parse_args().release.resolve()
    protocol = json.loads((release / 'protocol.json').read_text())

    def status(stage, **fields):
        row = dict(stage=stage, time_unix=time.time(), **fields)
        (release / 'status.json').write_text(json.dumps(row, indent=2) + '\n')
        print(json.dumps(row), flush=True)

    with (release / '.run.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        check_runtime(protocol)
        for model in protocol['models']:
            check_pins(protocol, model)
            todo = [(t, s) for t, s in grid(protocol) if not verify_cell(release, model, t, s)['complete']]
            if not todo:
                continue
            tag = model['tag']
            status('server_starting', model=model['id'], cells=len(todo))
            with served(model, release / f'test.{tag}.server.log'):
                warm_up(release, model, release / f'test.{tag}.warmup.jsonl')
                for temperature, seed in todo:
                    status('running', model=model['id'], temperature=temperature, seed=seed)
                    cell = stem(tag, temperature, seed)
                    with (release / f'{cell}.runner.log').open('a') as log:
                        subprocess.run([sys.executable, '-u', str(release / 'code/runner.py'),
                            '--model', model['id'], '--pairs', str(release / 'test.pairs.jsonl'),
                            '--kb', str(release / 'kb.jsonl'), '--out', str(release / f'{cell}.results.jsonl'),
                            '--seed', str(seed), '--temperature', str(temperature), '--top-p', '1.0'],
                            env=dict(os.environ, **SERVER_ENV), stdout=log, stderr=subprocess.STDOUT, check=True)
                    result = verify_cell(release, model, temperature, seed)
                    if not result['complete']:
                        raise RuntimeError(f'{cell} incomplete; inspect recorded transport errors before resuming')
                    status('cell_complete', model=model['id'], temperature=temperature, seed=seed,
                           json_validity=result['json_validity'])
            check_pins(protocol, model)
        status('grid_complete')


if __name__ == '__main__':
    # SIGTERM must unwind through served() or the vLLM server outlives the batch.
    def interrupted(signum, frame):
        raise KeyboardInterrupt(signum)
    signal.signal(signal.SIGTERM, interrupted)
    main()
