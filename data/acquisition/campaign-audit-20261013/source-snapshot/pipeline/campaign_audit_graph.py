"""Reconstruct a verifiable spanning forest for an existing campaign partition."""
from collections import defaultdict, deque
from array import array

from campaign import find, union


def covered_candidates(counts, postings, index):
    covered = defaultdict(int)
    for token, count in counts.items():
        occurrences = postings[token]
        for offset in range(0, len(occurrences), 2):
            other, other_count = occurrences[offset], occurrences[offset + 1]
            if other > index:
                covered[other] += count + other_count
    return covered


def exact_forest(items):
    parent = {row['id']: row['id'] for row in items}
    owners, edges = {}, []
    for row in items:
        for field in ('reports', 'added_hashes'):
            for value in sorted(set(row.get(field, []))):
                owner = owners.setdefault((field, value), row['id'])
                if find(parent, owner) != find(parent, row['id']):
                    edges.append(dict(left=owner, right=row['id'], criterion=field, value=value))
                    union(parent, owner, row['id'])
    return parent, edges


def complete_forest(items, frozen, fingerprints, progress=lambda _: None):
    if {r['id'] for r in items} != set(frozen) or len(items) != len(frozen):
        raise ValueError('Material IDs must match the frozen partition exactly once')
    parent, edges = exact_forest(items)
    for edge in edges:
        if frozen[edge['left']] != frozen[edge['right']]:
            raise ValueError('An exact link crosses the frozen partition')
    groups = defaultdict(list)
    for row in items:
        groups[frozen[row['id']]].append(row)
    comparisons = 0
    for root, rows in sorted(groups.items(), key=lambda pair: (-len(pair[1]), pair[0])):
        components = len({find(parent, row['id']) for row in rows})
        if components == 1:
            continue
        unique, code_totals = {}, {}
        for row in rows:
            key = row['code_key']
            if key not in unique:
                unique[key] = row
                code_totals[key] = fingerprints[key]['total']
            owner = unique[key]
            if code_totals[key] and find(parent, owner['id']) != find(parent, row['id']):
                edges.append(dict(left=owner['id'], right=row['id'], criterion='dolos',
                                  score=1.0, left_code=key, right_code=key))
                union(parent, owner['id'], row['id'])
                components -= 1
        if components == 1:
            continue
        # Identical nonempty code is linked above; compare each excerpt once.
        # Small excerpts first avoid repeated dense comparisons of bundled code.
        rows = sorted((r for k, r in unique.items() if code_totals[k]),
                      key=lambda r: (code_totals[r['code_key']], r['id']))
        postings = defaultdict(lambda: array('I'))
        totals = []
        for index, row in enumerate(rows):
            fingerprint = fingerprints[row['code_key']]
            totals.append(fingerprint['total'])
            for token, count in fingerprint['counts'].items():
                postings[token].extend((index, count))
        progress(dict(root=root, indexed=len(rows), components=components))
        for index, left in enumerate(rows):
            if components == 1:
                break
            covered = covered_candidates(fingerprints[left['code_key']]['counts'], postings, index)
            for other in sorted(covered):
                right = rows[other]
                if find(parent, left['id']) == find(parent, right['id']):
                    continue
                comparisons += 1
                score = covered[other] / (totals[index] + totals[other])
                if score < 0.5:
                    continue
                edges.append(dict(left=left['id'], right=right['id'], criterion='dolos',
                                  score=score, left_code=left['code_key'], right_code=right['code_key']))
                union(parent, left['id'], right['id'])
                components -= 1
                if components == 1:
                    break
            if index % 25 == 0:
                progress(dict(root=root, examined=index + 1, remaining_components=components,
                              comparisons=comparisons))
        if components != 1:
            raise ValueError(f'Cannot reconstruct {root}: {components} disconnected components')
    assigned = {key: find(parent, key) for key in parent}
    if assigned != frozen:
        raise ValueError('Witness forest does not reproduce the frozen partition')
    return edges, comparisons


def exposure_paths(edges, exposed, targets):
    adjacent = defaultdict(list)
    for index, edge in enumerate(edges):
        adjacent[edge['left']].append((edge['right'], index))
        adjacent[edge['right']].append((edge['left'], index))
    reached = {key: (None, None) for key in sorted(exposed)}
    queue = deque(reached)
    while queue:
        identity = queue.popleft()
        for neighbour, edge in adjacent[identity]:
            if neighbour not in reached:
                reached[neighbour] = (identity, edge)
                queue.append(neighbour)
    paths = []
    for target in sorted(targets):
        if target not in reached:
            raise ValueError(f'No exposure witness for {target}')
        identity, trail = target, []
        while reached[identity][0] is not None:
            identity, edge = reached[identity]
            trail.append(edge)
        paths.append(dict(id=target, exposed_item=identity, edge_indices=trail))
    return paths
