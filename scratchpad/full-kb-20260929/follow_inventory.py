"""Inventory complete download records in bounded offline batches."""
import json
import subprocess
import time
from pathlib import Path

ROOT = Path('~/intendiff_rag')
ACQ = ROOT / 'data/acquisition'
SOURCE = ACQ / 'datadog.intent-full.jsonl'
OUTPUT = ACQ / 'datadog.inventory-full.jsonl'
STATE = ACQ / 'full-kb-acquisition-state.json'


def records(path):
    with path.open() as stream:
        return [json.loads(line) for line in stream if line.endswith('\n') and line.strip()]


expected = len(records(ACQ / 'datadog.intent-full.pool.jsonl'))
previous = -1
changed = time.monotonic()
while True:
    downloaded = records(SOURCE)
    latest = {row['id']: row for row in records(OUTPUT)}
    known = {key for key, row in latest.items() if row['kind'] == 'malicious_intent'}
    pending = [row for row in downloaded if row['id'] not in known]
    state = {'expected': expected, 'download_records': len(downloaded),
             'inventoried': len(known), 'inventory_errors': sum(bool(latest[k].get('error')) for k in known),
             'status': 'acquiring', 'updated_unix': time.time()}
    if len(known) == expected:
        state['status'] = 'inventory_complete_with_reported_exclusions'
    temporary = STATE.with_suffix('.tmp')
    temporary.write_text(json.dumps(state, indent=2) + '\n')
    temporary.replace(STATE)
    print(json.dumps(state), flush=True)
    if len(known) == expected:
        break
    if len(downloaded) != previous:
        previous, changed = len(downloaded), time.monotonic()
    if not pending or (len(pending) < 200 and len(downloaded) < expected):
        if time.monotonic() - changed > 1800:
            raise RuntimeError('download made no progress for 30 minutes')
        time.sleep(30)
        continue
    batch = pending[:1000]
    manifest = ACQ / 'datadog.intent-extract-batch.jsonl'
    manifest.write_text(''.join(json.dumps(row) + '\n' for row in batch))
    command = ['docker', 'run', '--rm', '--network', 'none', '--read-only',
               '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
               '--user', '1000:1000', '--memory', '6g', '--cpus', '4',
               '--tmpfs', '/tmp:rw,noexec,nosuid,size=512m',
               '-v', f'{ROOT}:/workspace:ro',
               '-v', f'{ROOT}/data/work:/workspace/data/work',
               '-v', f'{ACQ}:/workspace/data/acquisition', '-w', '/workspace',
               'intendiff-preprocess:campaign-v1', 'python', '-u',
               'pipeline/datadog_corpus.py', '--manifest',
               'data/acquisition/datadog.intent-extract-batch.jsonl', '--into',
               'data/work/datadog-full', '--out', 'data/acquisition/datadog.inventory-full.jsonl']
    with (ACQ / 'datadog-inventory-full.log').open('a') as log:
        subprocess.run(command, check=True, stdout=log, stderr=subprocess.STDOUT)
