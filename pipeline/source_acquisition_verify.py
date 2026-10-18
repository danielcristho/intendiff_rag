"""Usage: python pipeline/source_acquisition_verify.py --prep DIR (offline)."""
import argparse
import hashlib
import json
from pathlib import Path

from external_mal import GUO_TIMES, guo_versions
from samples import load_jsonl


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def tree_digest(root):
    root = Path(root)
    result = hashlib.sha256()
    for path in sorted(p for p in root.rglob('*') if p.is_file()):
        result.update(str(path.relative_to(root)).encode() + b'\0')
        result.update(bytes.fromhex(digest(path)))
    return result.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--prep', type=Path, required=True)
    args = parser.parse_args()
    prep = args.prep
    source = Path('data/acquisition/external-mal-20261014')
    files = [GUO_TIMES, prep / 'mal.candidates.jsonl', source / 'pair-candidates.jsonl',
             source / 'archives.before.jsonl', source / 'extracted.before.jsonl',
             prep / 'guo-targets/archives.after.jsonl', prep / 'guo-targets/extracted.after.jsonl',
             prep / 'advisories.after.jsonl', source / 'advisories.before.jsonl']
    pins = {str(p): digest(p) for p in files}
    ids = {r['id'] for r in guo_versions()}
    archives = {side: {(r['name'], r['version']): r for r in load_jsonl(path)} for side, path in (
        ('before', source / 'archives.before.jsonl'), ('after', prep / 'guo-targets/archives.after.jsonl'))}
    trees = {side: {(r['name'], r['version']): r for r in load_jsonl(path)} for side, path in (
        ('before', source / 'extracted.before.jsonl'), ('after', prep / 'guo-targets/extracted.after.jsonl'))}
    pairs = load_jsonl(prep / 'mal.candidates.jsonl')
    for pair in pairs:
        if pair['id'] not in ids or pair['source_label'] != 'malicious':
            raise ValueError('Label identity absent from original Guo source list')
        path = Path(pair['metadata_file'])
        pins[str(path)] = digest(path)
        if pins[str(path)] != pair['metadata_sha256']:
            raise ValueError('Registry metadata changed')
        for side in ('before', 'after'):
            key = pair['name'], pair[side]
            archive, extracted = archives[side][key], trees[side][key]
            actual = digest(archive['tarball'])
            if actual != pair['sha256_' + side] or actual != extracted['sha256']:
                raise ValueError('Archive hash differs from pair or extraction')
            pins[archive['tarball']] = actual
            if pair[side + '_dir'] != extracted['dir'] or tree_digest(extracted['dir']) != extracted['tree_sha256']:
                raise ValueError('Extracted source tree changed')
    previous = {r['path']: r['sha256'] for r in load_jsonl('data/acquisition/campaign-audit-20261013/input-pins.jsonl')}
    current = load_jsonl(prep / 'campaigns-with-reports/input-pins.jsonl')
    shared = [r for r in current if r['path'] in previous]
    if any(r['sha256'] != previous[r['path']] for r in shared):
        raise ValueError('Inherited campaign fingerprint inputs changed')
    old_artifacts = json.loads(Path('data/acquisition/campaign-audit-20261013/artifact-manifest.json').read_text())['files']
    index = next(r for r in old_artifacts if r['path'].endswith('/material-index.jsonl'))
    if digest(index['path']) != index['sha256']:
        raise ValueError('Inherited campaign material index changed')
    report = dict(verified=True, source_label_identities=len(pairs), archive_and_tree_checks=len(pairs) * 2,
                  inherited_campaign_pins_matched=len(shared), sample_execution=False,
                  input_pins=[dict(path=p, sha256=h) for p, h in sorted(pins.items())])
    (prep / 'acquisition-verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'input_pins'}), flush=True)


if __name__ == '__main__':
    main()
