"""Resume the frozen development experiment only after CUDA initializes."""
import datetime
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
code = '''import ctypes, torch
driver = ctypes.CDLL('/usr/lib/wsl/lib/libcuda.so.1')
driver.cuInit.argtypes = [ctypes.c_uint]
driver.cuInit.restype = ctypes.c_int
result = driver.cuInit(0)
print('cuInit:', result, flush=True)
assert result == 0
torch.cuda.init()
value = torch.ones(1, device='cuda') + 1
torch.cuda.synchronize()
assert value.item() == 2
print(torch.cuda.get_device_name(0), flush=True)
'''
stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
try:
    result = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True, timeout=60)
    report = {'utc': stamp, 'returncode': result.returncode,
              'stdout': result.stdout, 'stderr': result.stderr}
except subprocess.TimeoutExpired:
    report = {'utc': stamp, 'timeout': True}
(HERE / f'resume-probe-{stamp}.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2), flush=True)
if report.get('returncode') != 0:
    raise SystemExit('CUDA still unavailable; no inference was started')
subprocess.run([sys.executable, '-u', str(ROOT / 'data/evaluation/evidence-dev-20261001/evaluate.py')],
               cwd=ROOT, check=True)
