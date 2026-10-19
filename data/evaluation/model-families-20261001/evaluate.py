"""Run the pinned exploratory baselines sequentially on one local GPU."""
import json
import fcntl
import os
import signal
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path('~/intendiff_rag')
HERE = Path(__file__).resolve().parent
PYTHON = ROOT / '.venv/bin/python'
PROTOCOL = json.loads((HERE / 'protocol.json').read_text())
STATUS = HERE / 'status.json'
LOCK = (HERE / '.evaluation.lock').open('w')
fcntl.flock(LOCK, fcntl.LOCK_EX | fcntl.LOCK_NB)

def terminate(signum, frame):
    raise KeyboardInterrupt(f'received signal {signum}')

signal.signal(signal.SIGTERM, terminate)


def status(stage, **fields):
    record = {'stage': stage, 'updated_unix': time.time(), 'scope': PROTOCOL['scope'], **fields}
    temporary = STATUS.with_suffix('.tmp')
    temporary.write_text(json.dumps(record, indent=2) + '\n')
    temporary.replace(STATUS)
    with (HERE / "evaluation.log").open("a") as stream:
        stream.write(json.dumps(record) + "\n")
    print(json.dumps(record), flush=True)


def records(path):
    if not path.exists():
        return []
    with path.open() as stream:
        return [json.loads(line) for line in stream if line.endswith('\n') and line.strip()]


def stop(process):
    if process is None or process.poll() is not None:
        return
    os.killpg(process.pid, signal.SIGTERM)
    try:
        process.wait(timeout=30)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait(timeout=30)


def run_model(model):
    result_path = HERE / f'{model["tag"]}.results.jsonl'
    expected = PROTOCOL['pair_count'] * len(PROTOCOL['configs'])
    newest = {row['run_key']: row for row in records(result_path)}
    if len(newest) == expected and not any(row.get('error') for row in newest.values()):
        return
    with socket.socket() as connection:
        if connection.connect_ex(('127.0.0.1', 8101)) == 0:
            raise RuntimeError('port 8101 is occupied; no existing service was stopped')
    command = [str(ROOT / '.venv/bin/vllm'), 'serve', model['path'],
               '--served-model-name', model['id'], '--host', '127.0.0.1', '--port', '8101',
               '--dtype', 'bfloat16', '--max-model-len', '32768', '--seed', '0',
               '--generation-config', 'vllm', '--gpu-memory-utilization', str(PROTOCOL['gpu_memory_utilization']),
               '--kv-cache-memory-bytes', str(PROTOCOL['kv_cache_memory_bytes']),
               '--max-num-seqs', '1', '--enable-prefix-caching']
    environment = dict(os.environ, VLLM_USE_FLASHINFER_SAMPLER='0', HF_HUB_OFFLINE='1',
                       TOKENIZERS_PARALLELISM='false')
    server = runner = None
    try:
        with (HERE / f'{model["tag"]}.server.log').open('a') as log:
            server = subprocess.Popen(command, cwd=ROOT, env=environment, stdout=log,
                                      stderr=subprocess.STDOUT, start_new_session=True)
        status('server_starting', model=model['id'], server_pid=server.pid, command=command)
        deadline = time.monotonic() + 1800
        while time.monotonic() < deadline:
            if server.poll() is not None:
                raise RuntimeError(f'model server exited with {server.returncode}')
            try:
                with urllib.request.urlopen('http://127.0.0.1:8101/v1/models', timeout=3) as response:
                    names = [entry['id'] for entry in json.load(response)['data']]
                if model['id'] in names:
                    break
            except OSError:
                pass
            time.sleep(2)
        else:
            raise RuntimeError('model startup exceeded 30 minutes')
        subprocess.run([str(PYTHON), str(HERE / 'server_check.py'), model['id']], cwd=ROOT, check=True)
        for attempt in range(2):
            command = [str(PYTHON), '-u', str(HERE / 'runner.py'), '--model', model['id'],
                       '--base-url', 'http://127.0.0.1:8101', '--pairs', str(HERE / 'pairs.jsonl'),
                       '--kb', str(HERE / 'kb.jsonl'), '--configs', ','.join(PROTOCOL['configs']),
                       '--seed', '0', '--temperature', '0', '--top-p', '1', '--timeout', '180',
                       '--out', str(result_path)]
            with (HERE / f'{model["tag"]}.runner.log').open('a') as log:
                runner = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
                                          start_new_session=True)
            while runner.poll() is None:
                rows = records(result_path)
                newest = {row['run_key']: row for row in rows}
                status('evaluating', model=model['id'], attempt=attempt + 1,
                       completed=sum(not row.get('error') for row in newest.values()),
                       expected=expected, invalid=sum(not row.get('json_valid') and not row.get('error')
                                                      for row in newest.values()), runner_pid=runner.pid)
                if server.poll() is not None:
                    raise RuntimeError('model server stopped during evaluation')
                if len(rows) >= 3 and all(row.get('error') for row in rows[-3:]):
                    raise RuntimeError('three consecutive request failures; evaluation stopped for inspection')
                time.sleep(20)
            if runner.returncode:
                raise RuntimeError(f'runner exited with {runner.returncode}')
            newest = {row['run_key']: row for row in records(result_path)}
            if len(newest) == expected and not any(row.get('error') for row in newest.values()):
                status('model_complete', model=model['id'], completed=expected)
                return
        raise RuntimeError('evaluation still has missing runs or transport errors after retry')
    finally:
        stop(runner)
        stop(server)


try:
    subprocess.run([str(PYTHON), str(HERE / 'preflight.py')], cwd=ROOT, check=True)
    for selected in PROTOCOL['models']:
        run_model(selected)
    subprocess.run([str(PYTHON), str(HERE / 'summarize.py')], cwd=ROOT, check=True)
    subprocess.run([str(PYTHON), str(HERE / 'compare.py')], cwd=ROOT, check=True)
    status('complete', completed=PROTOCOL['expected_runs'], human_annotation_verified=False)
except BaseException as error:
    status('error', error=str(error))
    raise
