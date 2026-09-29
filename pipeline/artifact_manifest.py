"""Record SHA-256 checksums of an explicit set of research artifacts.

    python pipeline/artifact_manifest.py --out manifest.json FILE [FILE ...]
"""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def write_manifest(output, paths):
    output = Path(output)
    records = []
    for path in sorted({Path(p) for p in paths}):
        if path.resolve() == output.resolve():
            raise ValueError('a manifest cannot include itself')
        with path.open('rb') as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        records.append({'path': str(path), 'bytes': path.stat().st_size, 'sha256': digest})
    document = {'generated_at_utc': datetime.now(timezone.utc).isoformat(),
                'scope': 'Explicit artifact snapshot; not a final dataset or design freeze.',
                'files': records}
    temporary = output.with_suffix('.tmp')
    temporary.write_text(json.dumps(document, indent=2) + '\n')
    temporary.replace(output)
    return document


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True)
    parser.add_argument('files', nargs='+')
    args = parser.parse_args()
    print(json.dumps({'files': len(write_manifest(args.out, args.files)['files'])}))
