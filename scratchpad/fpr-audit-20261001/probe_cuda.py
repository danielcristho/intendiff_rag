"""Probe CUDA initialization in isolated processes without changing the system."""
import json
import platform
import subprocess
import sys
from pathlib import Path

checks = {}
commands = {
    'driver_init_without_torch': 'import ctypes; x=ctypes.CDLL("libcuda.so.1"); print("library_loaded", flush=True); print(x.cuInit(0), flush=True)',
    'torch_init': 'import torch; print(torch.__version__, torch.version.cuda, flush=True); torch.cuda.init(); print(torch.cuda.get_device_name(0), flush=True)',
    'nvml': None,
}
for name, script in commands.items():
    command = [sys.executable, '-c', script] if script else ['nvidia-smi', '--query-gpu=name,memory.total,memory.used,driver_version', '--format=csv']
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=30)
        checks[name] = {'returncode': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}
    except subprocess.TimeoutExpired:
        checks[name] = {'timeout': True}
report = {'platform': platform.platform(), 'dxg_present': Path('/dev/dxg').exists(),
          'checks': checks, 'sample_execution': False, 'llm_calls': 0}
path = Path(__file__).resolve().parent / 'cuda-probe.json'
path.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2), flush=True)
