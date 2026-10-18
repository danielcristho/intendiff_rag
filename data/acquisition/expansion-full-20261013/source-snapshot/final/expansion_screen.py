"""Extract and screen expansion archives inside a network-disabled container."""
import argparse
import hashlib
import json
import tarfile
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import capability
from collect import HN_CATEGORIES
from samples import load_jsonl, unsafe_member
from typical import signal_categories
from wyss import write_jsonl


def inspect_archive(row, work):
    if row.get('error'):
        return row
    try:
        archive = Path(row['tarball'])
        if hashlib.sha256(archive.read_bytes()).hexdigest() != row['sha256']:
            raise ValueError('Archive checksum mismatch')
        key = hashlib.sha256(f"{row['name']}@{row['version']}".encode()).hexdigest()
        target = Path(work) / key
        target.mkdir(parents=True, exist_ok=True)
        with tarfile.open(archive) as tar:
            members = tar.getmembers()
            if len(members) > 20000 or sum(m.size for m in members) > 128 * 1024 * 1024:
                raise ValueError('Archive exceeds member count or expanded byte limit')
            for member in members:
                reason = unsafe_member(member)
                if reason or member.size > 16 * 1024 * 1024:
                    raise ValueError(f'Archive member rejected: {reason or "file byte limit"}')
            for member in members:
                if not member.isfile():
                    continue
                path = target / member.name
                path.parent.mkdir(parents=True, exist_ok=True)
                with tar.extractfile(member) as source:
                    path.write_bytes(source.read())
        roots = [p.parent for p in target.glob('*/package.json')]
        if (target / 'package.json').exists():
            roots.append(target)
        roots = [p for p in roots if capability.package_json(p).get('name') == row['name']
                 and str(capability.package_json(p).get('version', '')).split('+')[0]
                 == row['version'].split('+')[0]]
        if len(roots) != 1:
            raise ValueError('No unique package manifest matches the archive identity')
        root = roots[0]
        evidence = capability.explain_version(root)
        files = sorted(capability.text_files(root))
        digest = hashlib.sha256()
        for path in sorted(p for p in root.rglob('*') if p.is_file()):
            digest.update(str(path.relative_to(root)).encode() + b'\0')
            digest.update(hashlib.sha256(path.read_bytes()).digest())
        return dict(name=row['name'], version=row['version'], dir=str(root), sha256=row['sha256'],
                    tree_sha256=digest.hexdigest(), evidence=evidence,
                    capabilities=[s for s in capability.CAPABILITIES if s in evidence],
                    hooks=capability.install_commands(root),
                    dependencies=capability.declared_dependencies(root), text_files=files,
                    purpose_documents=[p for p in files if Path(p).name.lower().startswith(
                        ('readme', 'changelog', 'history'))])
    except Exception as exc:
        return dict(name=row['name'], version=row['version'], error=f'{type(exc).__name__}: {exc}')


def compare_versions(before, after):
    signals = set(after['capabilities']) - set(before['capabilities'])
    if after['hooks'] and before['hooks'] != after['hooks']:
        signals.add('install_script')
    delta = [s for s in capability.CAPABILITIES if s in signals]
    evidence = {s: after['evidence'][s] for s in delta}
    dependencies = [dict(dependency=name, before=before['dependencies'].get(name), after=spec)
                    for name, spec in after['dependencies'].items()
                    if name not in before['dependencies'] or
                    (before['dependencies'][name] != spec and capability.is_non_registry(spec))]
    if dependencies:
        delta.append('dependency_change')
        evidence['dependency_change'] = dependencies[:capability.MAX_EVIDENCE]
    old, new = set(before['text_files']), set(after['text_files'])
    if old and len(old - new) * 2 >= len(old):
        delta.append('large_deletion')
        evidence['large_deletion'] = [{'removed': len(old - new), 'of': len(old)}]
    return delta, evidence


def select_candidates(pairs, scans):
    screened, candidates = [], {}
    groups = {}
    for pair in pairs:
        versions = [scans.get((pair['name'], pair[side]), {}) for side in ('before', 'after')]
        errors = [v.get('error', 'missing_scan' if not v else None) for v in versions]
        if any(errors):
            row = dict(pair, errors=errors, screen_status='unavailable')
        else:
            before, after = versions
            delta, evidence = compare_versions(before, after)
            row = dict(pair, delta=delta, delta_evidence=evidence,
                       signal_categories=signal_categories(delta), screen_status='complete',
                       before_dir=before['dir'], after_dir=after['dir'],
                       sha256_before=before['sha256'], sha256_after=after['sha256'],
                       tree_sha256_before=before['tree_sha256'], tree_sha256_after=after['tree_sha256'],
                       purpose_documents_before=before['purpose_documents'],
                       purpose_documents_after=after['purpose_documents'])
        screened.append(row)
        for search in pair['searches']:
            groups.setdefault((pair['name'], search['search_category']), []).append(row)
    for (name, category), rows in groups.items():
        unavailable = []
        for row in sorted(rows, key=lambda r: r['pair_order']):
            if row['screen_status'] != 'complete':
                unavailable.append(row['id'])
                continue
            if not set(row['delta']) & HN_CATEGORIES[category]['signals']:
                continue
            candidate = candidates.setdefault(row['id'], dict(row, subset='HN',
                matched_search_categories=[], earlier_unavailable_pairs=[], gold_label=None,
                annotation_status='pending', holdout_eligible=False))
            candidate['matched_search_categories'].append(category)
            candidate['earlier_unavailable_pairs'] = sorted(set(
                candidate['earlier_unavailable_pairs'] + unavailable))
            break
    return screened, list(candidates.values())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True)
    parser.add_argument('--work', required=True)
    parser.add_argument('--workers', type=int, default=4)
    args = parser.parse_args()
    out = Path(args.out)
    scans = {(r['name'], r['version']): r for r in load_jsonl(out / 'version-scans.jsonl')}
    wanted = load_jsonl(out / 'archives.jsonl')
    pending = [r for r in wanted if (r['name'], r['version']) not in scans]
    with ProcessPoolExecutor(max_workers=args.workers) as pool, (out / 'version-scans.jsonl').open('a') as stream:
        futures = [pool.submit(inspect_archive, row, args.work) for row in pending]
        for index, future in enumerate(as_completed(futures), 1):
            row = future.result()
            stream.write(json.dumps(row) + '\n')
            stream.flush()
            scans[(row['name'], row['version'])] = row
            if index % 50 == 0 or index == len(pending):
                print(json.dumps({'scanned': len(scans), 'total': len(wanted),
                                  'errors': sum('error' in r for r in scans.values())}), flush=True)
    screened, candidates = select_candidates(load_jsonl(out / 'path-b-pairs.jsonl'), scans)
    write_jsonl(out / 'path-b-screened.jsonl', screened)
    write_jsonl(out / 'hn-candidates.jsonl', candidates)
    wanted = {(r['name'], r[side]) for r in candidates for side in ('before', 'after')}
    wanted.update((r['name'], r[side]) for r in load_jsonl(out / 'typical-candidates.jsonl')
                  for side in ('before', 'after'))
    write_jsonl(out / 'wanted.advisories.jsonl', [dict(name=n, version=v) for n, v in sorted(wanted)])
    print(json.dumps({'pairs_screened': len(screened), 'candidate_pairs': len(candidates),
                      'candidate_packages': len({r['name'] for r in candidates}),
                      'earlier_pair_unavailable': sum(bool(r['earlier_unavailable_pairs']) for r in candidates),
                      'human_labels_created': 0}), flush=True)


if __name__ == '__main__':
    main()
