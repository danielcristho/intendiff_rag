"""Summarize new source-MAL results alongside historical unlabelled HN controls."""
import json
import statistics
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent


def state(row):
    return row['parsed']['verdict'] if row['json_valid'] else 'invalid'


def summarize(rows, cohort):
    counts = Counter(state(r) for r in rows)
    result = {'cohort': cohort, 'n': len(rows), 'valid': len(rows) - counts['invalid'],
              'positive': counts['malicious'], 'invalid': counts['invalid'],
              'length': sum(r['finish_reason'] == 'length' for r in rows),
              'prompt_tokens': sum(r['usage']['prompt_tokens'] for r in rows),
              'completion_tokens': sum(r['usage']['completion_tokens'] for r in rows),
              'median_latency_ms': statistics.median(r['latency_ms'] for r in rows)}
    if cohort == 'MAL':
        result['source_recall_proxy'] = counts['malicious'] / len(rows)
        result['invalid_as_malicious_proxy'] = (counts['malicious'] + counts['invalid']) / len(rows)
    else:
        result['fpr'] = None
        result['label_status'] = 'unknown; alarms are not verified false positives'
    cited = [r['citation_audit'] for r in rows if r.get('citation_audit')]
    result['citation_diagnostics'] = {
        'responses': len(cited), 'unknown_ids': sum(bool(a['unknown_ids']) for a in cited),
        'no_content': sum(a['content_line_count'] == 0 for a in cited),
        'with_header_or_hunk': sum(any(x['kind'] in ('metadata', 'hunk') for x in a['referenced_lines']) for a in cited)}
    return result


def main():
    read = lambda name: [json.loads(l) for l in (HERE / name).open()]
    protocol = json.loads((HERE / 'protocol.json').read_text())
    cohorts = {'MAL': (read('pairs.jsonl'), read('results.jsonl')),
               'HN': (read('hn-historical-pairs.jsonl'), read('hn-historical-results.jsonl'))}
    groups, transitions, changed = [], [], []
    for cohort, (pairs, rows) in cohorts.items():
        index = {(r['pair_id'], r['arm']): r for r in rows}
        assert len(rows) == len(index) == 160
        assert set(index) == {(p['id'], a) for p in pairs for a in protocol['arms']}
        assert not any(r.get('transport_error') for r in rows)
        assert all(r['usage']['prompt_tokens'] == r['expected_prompt_tokens'] for r in rows)
        for arm in protocol['arms']:
            groups.append({'arm': arm, **summarize([r for r in rows if r['arm'] == arm], cohort)})
        for before, after in [('LEGACY-I', 'SCHEMA-I'), ('SCHEMA-I', 'IDS-I'),
                              ('IDS-D', 'IDS-I'), ('IDS-I', 'VERIFY-I')]:
            counts = Counter()
            for pair in pairs:
                a, b = index[pair['id'], before], index[pair['id'], after]
                counts[state(a), state(b)] += 1
                if state(a) != state(b):
                    changed.append({'cohort': cohort, 'pair_id': pair['id'], 'before': before, 'after': after,
                                    'before_state': state(a), 'after_state': state(b),
                                    'before_parsed': a['parsed'], 'after_parsed': b['parsed']})
            transitions.append({'cohort': cohort, 'before': before, 'after': after,
                                'counts': [{'before': a, 'after': b, 'n': n} for (a, b), n in sorted(counts.items())]})
    result = {'complete': True, 'new_generations': 160, 'historical_generations': 160,
              'human_annotation_verified': False, 'scope': protocol['scope'],
              'groups': groups, 'transitions': transitions}
    (HERE / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
    (HERE / 'changed-verdicts.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in changed))
    lines = ['# Hasil dev campuran D87', '',
             '32 kandidat MAL berlabel sumber baru diuji; 32 kandidat HN memakai hasil historis D85.',
             'Recall adalah proxy label sumber. Jumlah alarm HN bukan FPR.', '',
             '| Arm | MAL positif / 32 | Recall sumber | Valid MAL | Alarm HN / 32 | Valid HN |',
             '|---|---:|---:|---:|---:|---:|']
    for arm in protocol['arms']:
        m, h = [next(g for g in groups if g['arm'] == arm and g['cohort'] == c) for c in ('MAL', 'HN')]
        lines.append(f"| {arm} | {m['positive']} | {100*m['source_recall_proxy']:.2f}% | {m['valid']} | {h['positive']} | {h['valid']} |")
    lines += ['', 'Invalid dipertahankan dan dihitung benign pada metrik utama; sensitivitas ada di summary.json.',
              'Cohort kecil dan telah terpapar; tidak ada klaim gold, manfaat RAG, atau uji hipotesis utama.']
    (HERE / 'report.md').write_text('\n'.join(lines) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
