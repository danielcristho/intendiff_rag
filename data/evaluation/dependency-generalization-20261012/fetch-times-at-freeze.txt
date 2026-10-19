"""Cache publication timestamps from the npm registry, without loading package code."""
import concurrent.futures
import hashlib
import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'data/evaluation/dependency-generalization-20261012'
rows = json.loads((HERE / 'availability-candidates.json').read_text())
names = sorted({r[k]['name'] for r in rows for k in ('pair', 'archive_record')})
cache = HERE / 'publication-times'
cache.mkdir(exist_ok=True)


def fetch(name):
    path = cache / (hashlib.sha256(name.encode()).hexdigest() + '.json')
    if path.exists():
        return json.loads(path.read_text())
    url = 'https://registry.npmjs.org/' + urllib.parse.quote(name, safe='@')
    req = urllib.request.Request(url, headers={'User-Agent': 'IntentDiff-RAG-research/1'})
    try:
        with urllib.request.urlopen(req, timeout=90) as response:
            raw = response.read(50 * 1024 * 1024 + 1)
        assert len(raw) <= 50 * 1024 * 1024
        document = json.loads(raw)
        assert document['name'] == name
        record = {'name': name, 'time': document.get('time', {}), 'source': url,
                  'response_sha256': hashlib.sha256(raw).hexdigest(),
                  'retrieved_at': datetime.now(timezone.utc).isoformat()}
        path.write_text(json.dumps(record, indent=2) + '\n')
        return record
    except Exception as error:
        return {'name': name, 'error': repr(error), 'source': url}


with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    results = list(pool.map(fetch, names))
errors = [r for r in results if 'error' in r]
print(json.dumps({'requested': len(names), 'success': len(results)-len(errors), 'errors': errors}))
if errors:
    raise SystemExit(1)
