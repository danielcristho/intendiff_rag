"""Start one local server, run the frozen development batch, then stop it."""
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
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def status(stage, **fields):
    record = {'stage': stage, 'unix': time.time(), **fields}
    (HERE / 'status.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps(record), flush=True)


def verify(protocol):
    for section in ['source_sha256', 'upstream_sha256', 'model_sha256']:
        for name, expected in protocol[section].items():
            hasher = hashlib.sha256()
            with (ROOT / name).open('rb') as stream:
                for chunk in iter(lambda: stream.read(8 * 1024**2), b''):
                    hasher.update(chunk)
            assert hasher.hexdigest() == expected, name


def interrupted(signum, frame):
    raise KeyboardInterrupt(signum)


def main():
    with (HERE / '.evaluation.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        protocol = json.loads((HERE / 'protocol.json').read_text())
        verify(protocol)
        with socket.socket() as connection:
            if connection.connect_ex(('127.0.0.1', 8101)) == 0:
                raise RuntimeError('Port occupied; no existing service was stopped')
        command = [str(ROOT / '.venv/bin/vllm'), 'serve', protocol['model']['path'],
                   '--served-model-name', protocol['model']['id'], '--host', '127.0.0.1',
                   '--port', '8101', '--dtype', 'bfloat16', '--max-model-len', '32768',
                   '--seed', '0', '--generation-config', 'vllm', '--max-num-seqs', '1',
                   '--kv-cache-memory-bytes', str(protocol['kv_cache_memory_bytes']),
                   '--enable-prefix-caching']
        environment = dict(os.environ, HF_HUB_OFFLINE='1', TOKENIZERS_PARALLELISM='false',
                           VLLM_USE_FLASHINFER_SAMPLER='0')
        server = None
        try:
            with (HERE / 'server.log').open('a') as log:
                server = subprocess.Popen(command, cwd=ROOT, env=environment, stdout=log,
                                          stderr=subprocess.STDOUT, start_new_session=True)
            status('server_starting', pid=server.pid, command=command)
            for _ in range(600):
                if server.poll() is not None:
                    raise RuntimeError('Server exited; inspect server.log')
                try:
                    with urllib.request.urlopen('http://127.0.0.1:8101/v1/models', timeout=2) as response:
                        assert protocol['model']['id'] in [r['id'] for r in json.load(response)['data']]
                    break
                except OSError:
                    time.sleep(2)
            else:
                raise RuntimeError('Server startup timeout')
            status('evaluating')
            from run_batch import run
            run()
            verify(protocol)
            subprocess.run([sys.executable, str(HERE / 'summarize.py')], check=True, cwd=ROOT)
            status('complete', expected_generations=160, accuracy_metrics_available=False)
        except BaseException as error:
            status('error', error=repr(error))
            raise
        finally:
            if server is not None and server.poll() is None:
                os.killpg(server.pid, signal.SIGTERM)
                try:
                    server.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    os.killpg(server.pid, signal.SIGKILL)
                    server.wait(timeout=30)


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, interrupted)
    main()
