"""Load pinned request options from the experiment snapshot."""
import json
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=None)
def request_options(model):
    record = json.loads((Path(__file__).resolve().parent.parent / 'model-options.json').read_text())
    if record['model'] != model:
        raise ValueError('Request model differs from pinned options')
    return record['options']
