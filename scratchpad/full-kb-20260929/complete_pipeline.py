"""Finish full-pool preparation after acquisition; never start model inference."""
import json
import subprocess
import time
from pathlib import Path

ROOT = Path('~/intendiff_rag')
ACQ = ROOT / 'data/acquisition'
STATE = ACQ / 'full-kb-pipeline-state.json'
PYTHON = str(ROOT / '.venv/bin/python')


def state(stage, **fields):
    record = {'stage': stage, 'updated_unix': time.time(), **fields}
    temporary = STATE.with_suffix('.tmp')
    temporary.write_text(json.dumps(record, indent=2) + '\n')
    temporary.replace(STATE)
    print(json.dumps(record), flush=True)


def run(stage, command):
    state(stage)
    with (ACQ / f'full-kb-{stage}.log').open('w') as log:
        subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, check=True)


def container(memory, script, arguments, extra=()):
    return ['docker', 'run', '--rm', '--network', 'none', '--read-only',
            '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
            '--user', '1000:1000', '--memory', memory, '--cpus', '4',
            '--tmpfs', '/tmp:rw,noexec,nosuid,size=512m', *extra,
            '-v', f'{ROOT}:/workspace:ro',
            '-v', f'{ROOT}/data/work:/workspace/data/work',
            '-v', f'{ACQ}:/workspace/data/acquisition', '-w', '/workspace',
            'intendiff-preprocess:campaign-v1', 'python', '-u', script, *arguments]


try:
    state('waiting_for_inventory')
    while True:
        acquisition = json.loads((ACQ / 'full-kb-acquisition-state.json').read_text())
        if acquisition['status'] == 'inventory_complete_with_reported_exclusions':
            break
        if time.time() - acquisition['updated_unix'] > 1800:
            raise RuntimeError('inventory supervisor stopped updating for 30 minutes')
        time.sleep(30)
    run('verification', [PYTHON, '-u', 'pipeline/verify_kb_pool.py', '--acquisition', 'data/acquisition'])
    run('materials', container('6g', 'pipeline/campaign_materials.py', [
        '--acquisition', 'data/acquisition', '--inventory', 'datadog.inventory-full.jsonl',
        '--advisories', 'campaign-advisories-full.jsonl',
        '--out', 'data/work/audit/full.campaign-items.jsonl']))
    run('campaigns', container('18g', 'pipeline/campaign_fingerprints.py', [
        '--items', 'data/work/audit/full.campaign-items.jsonl',
        '--cache', 'data/work/audit/fingerprints', '--timeout', '600',
        '--scope', 'Available MAL plus full pinned KB pool; identity exclusions reported separately; incident verification pending',
        '--out', 'data/acquisition/combined-campaigns-full.json'],
        ['-e', 'NODE_OPTIONS=--max-old-space-size=12288']))
    campaigns = json.loads((ACQ / 'combined-campaigns-full.json').read_text())
    if not campaigns['complete_for_available_items'] or campaigns['failures']:
        raise RuntimeError('full-pool campaign fingerprinting has unresolved failures; review mapping was not replaced')
    run('review', [PYTHON, 'pipeline/review_package.py', '--acquisition', 'data/acquisition',
                   '--out-dir', 'data/review', '--campaigns', 'combined-campaigns-full.json'])
    state('prepared_for_human_review', final_test_set=False, llm_calls=0,
          items=campaigns['items'], clusters=campaigns['clusters'])
except BaseException as error:
    state('error', error=str(error))
    raise
