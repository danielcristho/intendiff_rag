"""Validate complete retrieval contrasts before any inference request."""
from collections import Counter

from configs import spec


def audit_retrieval(pairs, kb, configs, retrieve):
    issues, plan = [], []
    for kind, rows in (('pair', pairs), ('card', kb)):
        ids = [r.get('id') for r in rows]
        if any(not identity for identity in ids) or len(set(ids)) != len(ids):
            issues.append(dict(kind=kind, reason='missing_or_duplicate_ids'))
    if len(set(configs)) != len(configs):
        issues.append(dict(reason='duplicate_configs'))
    uses_cards = any(spec(config).cards for config in configs)
    if uses_cards:
        for kind, rows in (('pair', pairs), ('card', kb)):
            for row in rows:
                if not row.get('name') or not row.get('campaign'):
                    issues.append(dict(kind=kind, id=row.get('id'), reason='missing_exclusion_metadata'))
    if issues:
        return issues, plan
    for pair in pairs:
        chosen = {}
        for config in configs:
            cards = retrieve(config, pair, kb)
            chosen[config] = cards
            if Counter(c.get('label') for c in cards) != Counter(spec(config).cards):
                issues.append(dict(id=pair['id'], config=config, reason='incomplete_card_composition',
                                   expected=list(spec(config).cards), actual=[c.get('label') for c in cards]))
            plan.append(dict(pair_id=pair['id'], config=config, card_ids=[c['id'] for c in cards]))
        mb, no_intent = chosen.get('DIFF+I+MB'), chosen.get('DIFF+MB')
        if mb is not None and no_intent is not None and [c['id'] for c in mb] != [c['id'] for c in no_intent]:
            issues.append(dict(id=pair['id'], reason='intent_changes_retrieval'))
        mm = chosen.get('DIFF+I+MM')
        if mm is not None and mb is not None and len(mm) == len(mb) == 2:
            anchor = next(((i, c['id']) for i, c in enumerate(mb) if c['label'] == 'malicious'), None)
            if anchor is None or mm[anchor[0]]['id'] != anchor[1]:
                issues.append(dict(id=pair['id'], reason='mm_mb_primary_card_or_position_mismatch'))
    return issues, plan
