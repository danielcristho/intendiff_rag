"""Summarize development outputs without assigning unknown class labels."""
import json
import statistics
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
rows = [json.loads(l) for l in (HERE / 'results.jsonl').open()]
protocol = json.loads((HERE / 'protocol.json').read_text())
pairs = [json.loads(l) for l in (HERE / 'pairs.jsonl').open()]
expected = {(p['id'], arm) for p in pairs for arm in protocol['arms']}
index = {(r['pair_id'], r['arm']): r for r in rows}
assert len(rows) == len(index) == 160 and set(index) == expected
assert not any(r.get('transport_error') for r in rows)
assert all(r['expected_prompt_tokens'] == r['usage']['prompt_tokens'] for r in rows)
arms = []
for arm in protocol['arms']:
    selected = [r for r in rows if r['arm'] == arm]
    valid = [r for r in selected if r['json_valid']]
    entry = {'arm': arm, 'n': len(selected), 'valid': len(valid),
             'malicious_predictions': sum(r['parsed']['verdict'] == 'malicious' for r in valid),
             'length': sum(r['finish_reason'] == 'length' for r in selected),
             'prompt_tokens': sum(r['usage']['prompt_tokens'] for r in selected),
             'completion_tokens': sum(r['usage']['completion_tokens'] for r in selected),
             'median_latency_ms': statistics.median(r['latency_ms'] for r in selected)}
    if arm in ['IDS-I', 'IDS-D', 'VERIFY-I']:
        entry['unknown_id_responses'] = sum(bool(r['citation_audit']['unknown_ids']) for r in valid)
        entry['no_content_citation_responses'] = sum(r['citation_audit']['content_line_count'] == 0 for r in valid)
        entry['malicious_without_content_citation'] = sum(
            r['parsed']['verdict'] == 'malicious' and r['citation_audit']['content_line_count'] == 0 for r in valid)
    arms.append(entry)
transitions = []
for a, b in [('LEGACY-I', 'SCHEMA-I'), ('SCHEMA-I', 'IDS-I'), ('IDS-D', 'IDS-I'), ('IDS-I', 'VERIFY-I')]:
    counts = Counter()
    for p in pairs:
        records = [index[p['id'], arm] for arm in [a, b]]
        counts[tuple(r['parsed']['verdict'] if r['json_valid'] else 'invalid' for r in records)] += 1
    transitions.append({'before': a, 'after': b,
                        'counts': [{'before': x, 'after': y, 'n': n} for (x, y), n in sorted(counts.items())]})
result = {'complete': True, 'generations': len(rows), 'scope': protocol['scope'],
          'accuracy_metrics_available': False, 'reason': 'No independently verified human labels',
          'arms': arms, 'transitions': transitions,
          'verifier_total_tokens': sum(r['usage']['total_tokens'] for r in rows if r['arm'] in ['IDS-I', 'VERIFY-I'])}
(HERE / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
lines = ['# Hasil dev nyata D85', '',
         '32 kandidat HN tanpa gold manusia; 160 inferensi. Jumlah malicious adalah alarm, bukan FP.', '',
         '| Arm | JSON valid | Alarm malicious | Length | ID tidak ditemukan |',
         '|---|---:|---:|---:|---:|']
for a in arms:
    lines.append(f"| {a['arm']} | {a['valid']}/32 | {a['malicious_predictions']} | {a['length']} | {a.get('unknown_id_responses', 'N/A')} |")
lines += ['', 'VERIFY-I membutuhkan biaya IDS-I ditambah panggilan verifikasi.',
          'Keberadaan kutipan tidak membuktikan kebenaran alasan. Penurunan alarm bukan bukti penurunan FPR.',
          'Transisi lengkap, token, dan latency ada di summary.json.']
(HERE / 'report.md').write_text('\n'.join(lines) + '\n')
print(json.dumps(result, indent=2))
