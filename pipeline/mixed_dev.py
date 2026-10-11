"""Deterministic campaign-balanced selection for an exploratory review cohort."""
import hashlib


def rank(value):
    return hashlib.sha256(('D86|' + value).encode()).hexdigest()


def select_malicious_candidates(review, existing, count=32):
    eligible = [p for p in review if p.get('subset') == 'MAL'
                and not p.get('truncated', True) and p.get('diff')
                and 0 < p.get('diff_tokens', 0) <= 16000 and p.get('campaign')]
    ordered = sorted(eligible, key=lambda p: (rank(p['campaign']), rank(p['id'])))
    selected, campaigns = [], set()
    names = {p['name'] for p in existing}
    hashes = {p['diff_sha256'] for p in existing}
    archives = {p[k] for p in existing for k in ('sha256_before', 'sha256_after') if p.get(k)}
    for pair in ordered:
        versions = {pair[k] for k in ('sha256_before', 'sha256_after') if pair.get(k)}
        if (pair['campaign'] in campaigns or pair['name'] in names
                or pair['diff_sha256'] in hashes or versions & archives):
            continue
        selected.append(pair)
        campaigns.add(pair['campaign'])
        names.add(pair['name'])
        hashes.add(pair['diff_sha256'])
        archives.update(versions)
        if len(selected) == count:
            return selected, len(eligible)
    raise ValueError(f'Only {len(selected)} independent candidate groups available')


def blinded_pair(pair, review_id):
    allowed = ('name', 'before', 'after', 'diff', 'intent', 'delta', 'delta_evidence', 'truncated')
    return {**{key: pair[key] for key in allowed if key in pair},
            'id': review_id, 'annotation_status': 'pending', 'annotation_blinded': True}
