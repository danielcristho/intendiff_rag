"""Read-only CUDA loader probes; does not change drivers or restart WSL."""
import datetime
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
code = '''import ctypes
driver = ctypes.CDLL(%r)
driver.cuInit.argtypes = [ctypes.c_uint]
driver.cuInit.restype = ctypes.c_int
print("loaded", flush=True)
print("cuInit", driver.cuInit(0), flush=True)
'''
clean = {k: v for k, v in os.environ.items()
         if not k.startswith(('LD_', 'CUDA_', 'NVIDIA_', 'PYTHON'))}
cases = [
    ('venv_absolute', [sys.executable, '-c', code % '/usr/lib/wsl/lib/libcuda.so.1'], dict(os.environ)),
    ('system_python_clean', ['/usr/bin/python3', '-c', code % '/usr/lib/wsl/lib/libcuda.so.1'], clean),
    ('loader_trace', [sys.executable, '-c', code % '/usr/lib/wsl/lib/libcuda.so.1'], dict(clean, LD_DEBUG='libs')),
    ('wsl_version', ['/mnt/c/Windows/System32/wsl.exe', '--version'], dict(os.environ)),
]
results = []
for tag, command, environment in cases:
    try:
        completed = subprocess.run(command, env=environment, capture_output=True, timeout=30)
        output = completed.stdout.decode('utf-16-le' if tag == 'wsl_version' else 'utf-8', errors='replace')
        errors = completed.stderr.decode(errors='replace')
        (HERE / f'{tag}.stdout.log').write_text(output)
        (HERE / f'{tag}.stderr.log').write_text(errors)
        result = {'case': tag, 'returncode': completed.returncode, 'stdout': output,
                  'stderr_tail': errors[-1000:]}
    except (OSError, subprocess.TimeoutExpired) as error:
        result = {'case': tag, 'error': repr(error)}
    results.append(result)
    print(json.dumps(result), flush=True)
report = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'removed_variable_names': sorted(set(os.environ) - set(clean)),
          'cases': results, 'system_mutations': False, 'llm_calls': 0}
(HERE / 'diagnosis.json').write_text(json.dumps(report, indent=2) + '\n')
