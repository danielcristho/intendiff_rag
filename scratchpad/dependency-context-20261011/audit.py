"""Audit local dependency versions, publication times, archive bytes and retrieval leakage."""
import hashlib
import json
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'data/evaluation/dependency-context-20261011'
sys.path.insert(0, str(ROOT / 'pipeline'))
from runner import eligible


def read(path):
    return [json.loads(line) for line in path.open()]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def time(value):
    return datetime.fromisoformat(value.replace('Z', '+00:00'))


inventory = read(ROOT / 'data/acquisition/datadog.inventory-full.jsonl')
versions = sorted([r for r in inventory if r['name'] == 'easy-day-js'], key=lambda r: r['version'])
assert [r['version'] for r in versions] == ['1.11.21', '1.11.22']
mixed = read(ROOT / 'data/evaluation/mixed-dev-20261002/pairs.jsonl')
mal = read(ROOT / 'data/evaluation/mixed-validation-20261011/pairs.jsonl')
campaigns = json.loads((ROOT / 'data/acquisition/combined-campaigns-full.json').read_text())['campaigns']
version_records = []
for version in versions:
    archive, root = ROOT / version['archive'], ROOT / version['dir']
    assert sha(archive) == version['sha256']
    metadata = json.loads((ROOT / version['package_info'][0]).read_text())
    manifest = json.loads((root / 'package.json').read_text())
    files = {'package.json', manifest['main']}
    postinstall = manifest['scripts'].get('postinstall')
    if postinstall:
        assert postinstall == 'node setup.cjs --no-warnings'
        files.add('setup.cjs')
    hashes = {}
    with zipfile.ZipFile(archive) as z:
        for name in sorted(files):
            matches = [n for n in z.namelist() if n.endswith('/package/' + name)]
            assert len(matches) == 1, (name, matches)
            raw = (root / name).read_bytes()
            assert raw == z.read(matches[0], pwd=b"infected")
            hashes[name] = {'path': str(root / name), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
    version_records.append({'version': version['version'], 'name': version['name'],
        'published_at': metadata['time'][version['version']], 'postinstall': postinstall,
        'campaign': campaigns[version['id']], 'archive_sha256': sha(archive), 'archive': str(archive),
        'metadata_path': version['package_info'][0], 'metadata_sha256': sha(ROOT / version['package_info'][0]),
        'files': hashes})
requests, targets, exclusions = [], [], []
for pair in mixed:
    before = json.loads((ROOT / pair['before_dir'] / 'package.json').read_text())
    after = json.loads((ROOT / pair['after_dir'] / 'package.json').read_text())
    changed = []
    for section in ('dependencies', 'devDependencies', 'optionalDependencies', 'peerDependencies'):
        for name, constraint in after.get(section, {}).items():
            if before.get(section, {}).get(name) != constraint:
                changed.append({'section': section, 'name': name, 'constraint': constraint,
                                'before': before.get(section, {}).get(name)})
    exclusions.append({'pair_id': pair['id'], 'retrieval_exclude_names': sorted({r['name'] for r in changed}),
                       'reason': 'Direct changed dependency identity; exclude as labeled examples, not as unlabeled target context'})
    dependency = [r for r in changed if r['name'] == 'easy-day-js']
    if not dependency:
        continue
    assert pair['subset'] == 'MAL' and dependency == [{'section': 'dependencies', 'name': 'easy-day-js',
                                                     'constraint': '^1.11.21', 'before': None}]
    roots = ROOT / pair['after_dir']
    locks = [str(p.relative_to(roots)) for p in roots.rglob('*') if p.is_file()
             and p.name in ('package-lock.json', 'npm-shrinkwrap.json', 'yarn.lock', 'pnpm-lock.yaml')]
    targets.append({'pair_id': pair['id'], 'published_at': pair['published_at'], 'campaign': pair['campaign'],
                    'constraint': '^1.11.21', 'lockfiles': locks,
                    'versions': [{'version': v['version'],
                        'published_before_target': time(v['published_at']) <= time(pair['published_at']),
                        'old_retrieval_eligible': not any(pair.get(k) and pair.get(k) == v.get(k)
                                                         for k in ('name', 'campaign')),
                        'new_retrieval_eligible': eligible(pair, {'name': v['name'], 'campaign': v['campaign']})}
                        for v in version_records]})
    requests += [{'version': v['version'], 'range': '^1.11.21'} for v in versions]
semver = json.loads(subprocess.check_output(['node', str(Path(__file__).parent / 'semver-check.cjs')],
                                           input=json.dumps(requests).encode()))
assert len(targets) == 20 and all(r['satisfies'] for r in semver)
assert all(v['published_before_target'] for t in targets for v in t['versions'])
assert not any(t['lockfiles'] for t in targets)
report = {'targets': targets, 'dependency_versions': version_records, 'semver_checks': semver,
          'dependency_targets': 20, 'target_cluster_ids': len({t['campaign'] for t in targets}),
          'old_eligible_target_dependency_combinations': sum(v['old_retrieval_eligible'] for t in targets for v in t['versions']),
          'new_eligible_target_dependency_combinations': sum(v['new_retrieval_eligible'] for t in targets for v in t['versions']),
          'exact_installed_versions_verified': False, 'human_gold_verified': False,
          'real_verified_kb_cards': 0, 'kb_status': 'Only synthetic kb.sample.jsonl exists; no real verified cards available',
          'interpretation': 'Both archived versions satisfy the range and predate target publication; lack of lockfile leaves actual installation unresolved.'}
(OUT / 'dependency-audit.json').write_text(json.dumps(report, indent=2) + '\n')
(OUT / 'retrieval-exclusions.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in exclusions))
(OUT / 'pairs.jsonl').write_text(''.join(json.dumps(p, ensure_ascii=False) + '\n' for p in mal if p['id'] in {t['pair_id'] for t in targets}))
print(json.dumps({k: v for k, v in report.items() if k not in ('targets', 'dependency_versions', 'semver_checks')}, indent=2))
