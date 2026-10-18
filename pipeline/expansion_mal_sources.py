"""Inventory new source-labeled compromised versions at a pinned GitHub commit."""
import argparse
import hashlib
import json
import urllib.request
from pathlib import Path

from samples import load_jsonl
from wyss import write_jsonl

REPO = 'https://api.github.com/repos/DataDog/malicious-software-packages-dataset'


def cached(url, path):
    if not path.exists():
        request = urllib.request.Request(url, headers={'User-Agent': 'IntentDiff-RAG-research/1'})
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = response.read(64 * 1024 * 1024 + 1)
        if len(payload) > 64 * 1024 * 1024:
            raise ValueError('Metadata exceeds byte limit')
        path.write_bytes(payload)
    return json.loads(path.read_text())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    out = Path(args.out)
    cache = Path('data/upstream/expansion-20261012/datadog')
    cache.mkdir(parents=True, exist_ok=True)
    cutoff = json.loads((out / 'protocol.json').read_text())['cutoff']
    commit = cached(REPO + '/commits?per_page=1&until=' + cutoff,
                    cache / 'commits.json')[0]
    revision = commit['sha']
    manifest = cached('https://raw.githubusercontent.com/DataDog/malicious-software-packages-dataset/'
                      + revision + '/samples/npm/manifest.json', cache / 'manifest.json')
    listing = cached(REPO + '/contents/samples/npm?ref=' + revision, cache / 'npm-tree.json')
    tree_sha = next(r['sha'] for r in listing if r['name'] == 'compromised_lib')
    tree = cached(REPO + '/git/trees/' + tree_sha + '?recursive=1', cache / 'compromised-tree.json')
    if tree.get('truncated'):
        raise ValueError('Source tree is truncated')
    names = {name.replace('/', '@'): name for name in manifest}
    old = {r['id'] for r in load_jsonl('data/acquisition/datadog.compromised.pool.jsonl')}
    exposures = load_jsonl(out / 'exposure-registry.jsonl')
    exposed_names = {r['name'] for r in exposures}
    unique = {}
    for entry in sorted(tree['tree'], key=lambda r: r['path']):
        if not entry['path'].endswith('.zip'):
            continue
        folder, version, _ = entry['path'].split('/')
        name = names[folder]
        labels = manifest[name]
        if not isinstance(labels, list) or version not in labels:
            continue
        identity = f'{name}@{version}'
        if identity in old:
            continue
        unique.setdefault(identity, dict(id=identity, name=name, version=version,
            source_label='malicious', gold_label=None, annotation_status='pending',
            source_revision=revision, source_path='samples/npm/compromised_lib/' + entry['path'],
            git_blob_sha1=entry['sha'], bytes=entry['size'], package_exposed=name in exposed_names,
            predecessor_status='not_resolved', archive_status='not_downloaded',
            campaign_status='not_verified', holdout_eligible=False))
    rows = sorted(unique.values(), key=lambda r: hashlib.sha256(r['id'].encode()).hexdigest())
    write_jsonl(out / 'new-mal-source-versions.jsonl', rows)
    summary = dict(revision=revision, revision_date=commit['commit']['committer']['date'],
                   previous_source_versions=len(old), new_source_versions=len(rows),
                   new_package_names=len({r['name'] for r in rows}),
                   new_versions_with_unexposed_names=sum(not r['package_exposed'] for r in rows),
                   acquired_new_mal_pairs=0, verified_new_campaigns=0,
                   note='Source-version inventory only; predecessor, archives and campaigns remain pending.')
    (out / 'mal-source-summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
