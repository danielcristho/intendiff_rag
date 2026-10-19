"""Run seven pinned local models sequentially and audit each complete batch."""
import fcntl
import json
import os
import signal
import socket
import subprocess
import time
import urllib.request

from common import ARMS, HERE, ROOT, read_rows, validate_rows, write_json
from report import report
from run_batch import run
from verify import verify_model, verify_pins


def status(stage, **fields):
    record = {'stage': stage, 'updated_unix': time.time(), **fields}
    write_json(HERE / 'status.json', record)
    print(json.dumps(record), flush=True)


def stop(server):
    if server is None or server.poll() is not None:
        return
    os.killpg(server.pid, signal.SIGTERM)
    try:
        server.wait(timeout=30)
    except subprocess.TimeoutExpired:
        os.killpg(server.pid, signal.SIGKILL)
        server.wait(timeout=30)


def run_model(protocol, model):
    verify_pins(protocol, model)
    pairs = read_rows(HERE / 'pairs.jsonl')
    rows = read_rows(HERE / f"{model['tag']}.results.jsonl")
    seen = validate_rows(rows, model, pairs)
    if len(seen) == len(pairs) * len(ARMS):
        verify_model(model)
        return
    with socket.socket() as connection:
        if connection.connect_ex(('127.0.0.1', 8101)) == 0:
            raise RuntimeError('Port occupied; no unrelated service was stopped')
    command = [str(ROOT / '.venv/bin/vllm'), 'serve', model['path'],
        '--served-model-name', model['id'], '--host', '127.0.0.1', '--port', '8101',
        '--dtype', 'bfloat16', '--max-model-len', '32768', '--seed', '0',
        '--generation-config', 'vllm', '--max-num-seqs', '1',
        '--kv-cache-memory-bytes', '6442450944', '--enable-prefix-caching']
    environment = dict(os.environ, HF_HUB_OFFLINE='1', TOKENIZERS_PARALLELISM='false',
                       VLLM_USE_FLASHINFER_SAMPLER='0')
    server = None
    try:
        with (HERE / f"{model['tag']}.server.log").open('a') as log:
            server = subprocess.Popen(command, cwd=ROOT, env=environment,
                stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        status('server_starting', model=model['id'], pid=server.pid, command=command)
        for _ in range(900):
            if server.poll() is not None:
                raise RuntimeError('Server exited; inspect server log')
            try:
                with urllib.request.urlopen('http://127.0.0.1:8101/v1/models', timeout=2) as response:
                    assert model['id'] in [r['id'] for r in json.load(response)['data']]
                break
            except OSError:
                time.sleep(2)
        else:
            raise RuntimeError('Server startup timeout')
        status('evaluating', model=model['id'], expected_per_model=2919, total_expected=20433)
        run(model)
    finally:
        stop(server)
    verify_pins(protocol, model)
    verify_model(model)
    status('model_complete', model=model['id'], completed=2919)


def main():
    with (HERE / '.evaluation.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        protocol = json.loads((HERE / 'protocol.json').read_text())
        try:
            for model in protocol['models']:
                run_model(protocol, model)
                report()
            result = report()
            assert result['complete'] and len(result['groups']) == 21
            status('complete', new_generations=20433, models=7, pairs=973,
                   human_annotation_verified=False)
        except BaseException as error:
            status('error', error=repr(error))
            raise


if __name__ == '__main__':
    def interrupted(signum, frame):
        raise KeyboardInterrupt(signum)
    signal.signal(signal.SIGTERM, interrupted)
    main()
