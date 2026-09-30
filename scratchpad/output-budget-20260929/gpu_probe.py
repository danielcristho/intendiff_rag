"""Check CUDA initialization without loading samples or running inference."""
import os
from pathlib import Path
import torch

print({"dxg_exists": Path('/dev/dxg').exists(), "torch": torch.__version__,
       "cuda_build": torch.version.cuda,
       "environment": {key: os.environ.get(key) for key in
                       ('LD_LIBRARY_PATH', 'LD_PRELOAD', 'CUDA_VISIBLE_DEVICES')}}, flush=True)
torch.cuda.init()
print({"device": torch.cuda.get_device_name(0), "count": torch.cuda.device_count()}, flush=True)
