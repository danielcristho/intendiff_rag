"""Report conditional-version verdicts without claiming population recall or FPR."""
import json
import statistics
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent


def state(row):
    return row['parsed']['verdict'] if row['json_valid'] else 'invalid'


def main():
    rows = [json.loads(l) for l in (HERE / 'results.jsonl').open()]
    pairs = [json.loads(l) for l in (HERE / 'pairs.jsonl').open()]
    arms = ['CTX-1.11.21', 'CTX-1.11.22']
    index = {(r['pair_id'], r['arm']): r for r in rows}
    assert len(rows) == len(index) == 40
    assert set(index) == {(p['id'], a) for p in pairs for a in arms}
    assert not any(r.get('transport_error') for r in rows)
    groups = []
    for arm in arms:
        selected = [r for r in rows if r['arm'] == arm]
        counts = Counter(state(r) for r in selected)
        groups.append({'arm': arm, 'n': len(selected), 'verdicts': dict(counts),
                       'valid': sum(r['json_valid'] for r in selected),
                       'length': sum(r['finish_reason'] == 'length' for r in selected),
                       'unknown_id_responses': sum(bool(r.get('citation_audit', {}).get('unknown_ids')) for r in selected),
                       'dependency_citing_responses': sum(r.get('citation_audit', {}).get('dependency_citations', 0) > 0 for r in selected),
                       'prompt_tokens': sum(r['usage']['prompt_tokens'] for r in selected),
                       'completion_tokens': sum(r['usage']['completion_tokens'] for r in selected),
                       'median_latency_ms': statistics.median(r['latency_ms'] for r in selected)})
    transitions = Counter((state(index[p['id'], arms[0]]), state(index[p['id'], arms[1]])) for p in pairs)
    result = {'complete': True, 'generations': 40, 'scope': 'conditional dependency-version diagnostic',
              'human_gold_verified': False, 'installed_version_verified': False,
              'independent_dependency_families': 1, 'groups': groups,
              'version_transitions': [{'before': a, 'after': b, 'n': n} for (a,b),n in sorted(transitions.items())],
              'not_claimed': ['realized-installation recall', 'FPR', 'RAG benefit', 'independent 20-incident evidence']}
    (HERE / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
