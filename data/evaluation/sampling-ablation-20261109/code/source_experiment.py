"""Usage: python source_experiment.py --release DIR --stage dev|test."""
import argparse
import fcntl
import hashlib
import json
import os
import signal
import socket
import subprocess
import sys
import time
import urllib.request
from contextlib import contextmanager
from pathlib import Path

from source_results import verify
from runner import build, call_llm, load_jsonl, retrieve
from configs import CONFIGS


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def check_pins(protocol, model):
    for row in protocol['input_pins'] + model['pins']:
        if digest(row['path']) != row['sha256']:
            raise ValueError('Frozen input changed: ' + row['path'])


def stop(server):
    if server is None or server.poll() is not None:
        return
    os.killpg(server.pid, signal.SIGTERM)
    try:
        server.wait(timeout=30)
    except subprocess.TimeoutExpired:
        os.killpg(server.pid, signal.SIGKILL)
        server.wait(timeout=30)


SERVER_ENV = dict(HF_HUB_OFFLINE='1', TOKENIZERS_PARALLELISM='false', VLLM_USE_FLASHINFER_SAMPLER='0')


def serve_command(model):
    return [str(Path('.venv/bin/vllm').resolve()), 'serve', model['path'],
        '--served-model-name', model['id'], '--host', '127.0.0.1', '--port', '8101',
        '--dtype', 'bfloat16', '--max-model-len', str(model['max_model_len']), '--seed', '0',
        '--generation-config', 'vllm', '--max-num-seqs', '1',
        '--kv-cache-memory-bytes', str(model['kv_cache_memory_bytes']), '--enable-prefix-caching']


@contextmanager
def served(model, log_path):
    with socket.socket() as connection:
        if connection.connect_ex(('127.0.0.1', 8101)) == 0:
            raise RuntimeError('Model port 8101 is occupied')
    server = None
    try:
        with Path(log_path).open('a') as log:
            server = subprocess.Popen(serve_command(model), env=dict(os.environ, **SERVER_ENV),
                                      stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        for _ in range(450):
            if server.poll() is not None:
                raise RuntimeError('Model server exited')
            try:
                with urllib.request.urlopen('http://127.0.0.1:8101/v1/models', timeout=2) as response:
                    if model['id'] not in [r['id'] for r in json.load(response)['data']]:
                        raise ValueError('Unexpected served model')
                break
            except OSError:
                time.sleep(2)
        else:
            raise RuntimeError('Model startup timeout')
        yield server
    finally:
        stop(server)


# warm_up's replies are logged but never scored.
def warm_up(release, model, log_path):
    pair = load_jsonl(release / 'dev.pairs.jsonl')[0]
    cards = load_jsonl(release / 'kb.jsonl')
    for config in list(CONFIGS)[:3]:
        response = call_llm('http://127.0.0.1:8101', model['id'],
            build(config, pair, retrieve(config, pair, cards)), 0, 120,
            dict(temperature=0.0, top_p=1.0))
        with Path(log_path).open('a') as log:
            log.write(json.dumps(dict(pair_id=pair['id'], config=config, response=response)) + '\n')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--release', type=Path, required=True)
    parser.add_argument('--stage', choices=('dev', 'test'), required=True)
    args = parser.parse_args()
    out = args.release.resolve()
    protocol = json.loads((out / 'protocol.json').read_text())
    def status(stage, **fields):
        row = dict(stage=stage, time_unix=time.time(), **fields)
        (out / 'status.json').write_text(json.dumps(row, indent=2) + '\n')
        print(json.dumps(row), flush=True)
    with (out / '.run.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if args.stage == 'test':
            if protocol.get('test_released') is not True:
                raise ValueError('Test inputs have not passed release checks')
            for model in protocol['models']:
                dev = verify(out, 'dev', model)
                if not dev['complete'] or dev['json_validity'] < 0.9:
                    raise ValueError('Development format gate has not passed')
        for model in protocol['models']:
            check_pins(protocol, model)
            existing = verify(out, args.stage, model)
            if existing['complete']:
                continue
            status('server_starting', model=model['id'], experiment_stage=args.stage)
            with served(model, out / f'{args.stage}.{model["tag"]}.server.log'):
                status('running', model=model['id'], experiment_stage=args.stage)
                warm_up(out, model, out / f'{args.stage}.{model["tag"]}.warmup.jsonl')
                with (out / f'{args.stage}.{model["tag"]}.runner.log').open('a') as log:
                    subprocess.run([sys.executable, '-u', str(out / 'code/runner.py'), '--model', model['id'],
                        '--pairs', str(out / f'{args.stage}.pairs.jsonl'), '--kb', str(out / 'kb.jsonl'),
                        '--out', str(out / f'{args.stage}.{model["tag"]}.results.jsonl')],
                        env=dict(os.environ, **SERVER_ENV), stdout=log, stderr=subprocess.STDOUT, check=True)
            check_pins(protocol, model)
            result = verify(out, args.stage, model)
            if not result['complete']:
                raise RuntimeError('Batch incomplete; inspect recorded transport errors before resuming')
            status('model_complete', model=model['id'], experiment_stage=args.stage,
                   completed=result['completed'], json_validity=result['json_validity'])
        status('stage_complete', experiment_stage=args.stage)


if __name__ == '__main__':
    def interrupted(signum, frame):
        raise KeyboardInterrupt(signum)
    signal.signal(signal.SIGTERM, interrupted)
    main()
