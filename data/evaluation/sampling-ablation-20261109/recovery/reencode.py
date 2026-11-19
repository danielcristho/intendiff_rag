"""Losslessly re-encode results files whose rows contain Unicode line separators.

Usage: python reencode.py RELEASE BACKUP_DIR
"""
import json, shutil, sys
from pathlib import Path

release, backup = Path(sys.argv[1]), Path(sys.argv[2])
for path in sorted(release.glob('test.*.results.jsonl')):
    text = path.read_text(encoding='utf-8')
    lines = [l for l in text.split('\n') if l.strip()]
    if all(len(l.splitlines()) == 1 for l in lines):
        continue
    rows = [json.loads(l) for l in lines]
    out = ''.join(json.dumps(r) + '\n' for r in rows)
    assert [json.loads(l) for l in out.splitlines()] == rows
    shutil.copyfile(path, backup / path.name)
    path.write_text(out)
    print(f'reencoded {path.name}: {len(rows)} rows, original kept in {backup}', flush=True)
