"""Compare completed 2048-token runs with the frozen historical 512-token control."""
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
protocol = json.loads((HERE / 'protocol.json').read_text())
BASE = ROOT / protocol['baseline_directory']
pairs = {r['id']: r for r in map(json.loads, (HERE / 'pairs.jsonl').open())}
before_summary = json.loads((BASE / 'summary.json').read_text())
after_summary = json.loads((HERE / 'summary.json').read_text())
assert before_summary['complete'] and after_summary['complete']
before = list(map(json.loads, (BASE / 'results.jsonl').open()))
after = list(map(json.loads, (HERE / 'results.jsonl').open()))


def key(row):
    return row['model'], row['config'], row['pair_id']


def state(row):
    return row['verdict'] if row['json_valid'] else 'invalid'


old = {key(r): r for r in before}
new = {key(r): r for r in after}
assert len(old) == len(new) == len(before) == len(after) == 3892
assert old.keys() == new.keys()
for identity, row in new.items():
    reference = old[identity]
    assert not row.get('error') and row['max_tokens'] == 2048
    assert row['experiment_id'] == protocol['experiment_id']
    assert row['run_key'] == reference['run_key'] + '|max_tokens=2048'
    for field in ['model', 'config', 'pair_id', 'seed', 'temperature', 'top_p', 'top_k',
                  'label', 'truncated', 'cards', 'diff_sha256', 'prompt_tokens',
                  'evaluation_scope', 'label_origin', 'human_annotation_verified']:
        assert row[field] == reference[field], (identity, field)
    assert 0 < row['completion_tokens'] <= 2048 and row['prompt_tokens'] + 2048 <= 32768

groups = []
for model in protocol['models']:
    for config in protocol['configs']:
        identities = [k for k in old if k[:2] == (model['id'], config)]
        assert len(identities) == 973
        group = {'model': model['id'], 'config': config}
        for label, summary, source in [('baseline', before_summary, old), ('candidate', after_summary, new)]:
            metrics = next(g for g in summary['groups'] if g['model'] == model['id'] and g['config'] == config)
            assert metrics['completed'] == 973 and metrics['transport_errors'] == 0
            for subset, metric in [('MAL', 'mal_source_recall_proxy'), ('TYP', 'typ_assumed_benign_fpr')]:
                selected = [source[k] for k in identities if pairs[k[2]]['subset'] == subset]
                assert metrics[metric]['n'] == len(selected)
                assert metrics[metric]['positive'] == sum(state(r) == 'malicious' for r in selected)
            group[label] = metrics
        group['paired_transitions'] = {
            subset: dict(Counter(f'{state(old[k])}->{state(new[k])}' for k in identities
                                 if pairs[k[2]]['subset'] == subset)) for subset in ['MAL', 'TYP']}
        group['delta_percentage_points'] = {
            metric: 100 * (group['candidate'][metric]['rate'] - group['baseline'][metric]['rate'])
            for metric in ['mal_source_recall_proxy', 'typ_assumed_benign_fpr']}
        stopped = [k for k in identities if old[k]['finish_reason'] != 'length']
        limited = [k for k in identities if old[k]['finish_reason'] == 'length']
        group['response_reproducibility'] = {
            'baseline_stopped': len(stopped),
            'stopped_exact_raw_match': sum(old[k]['raw'] == new[k]['raw'] for k in stopped),
            'baseline_length_limited': len(limited),
            'length_limited_exact_text_prefix': sum(new[k]['raw'].startswith(old[k]['raw']) for k in limited)}
        groups.append(group)
result = {'complete': True, 'generated_at_utc': datetime.now(timezone.utc).isoformat(),
          'experiment_id': protocol['experiment_id'], 'scope': protocol['scope'],
          'historical_control': True, 'baseline_runs': 3892, 'new_runs': 3892,
          'human_annotation_verified': False, 'groups': groups}
(HERE / 'comparison.json').write_text(json.dumps(result, indent=2) + '\n')
lines = ['# Eksperimen batas keluaran 512 → 2.048 token', '',
         'Lengkap: 3.892 run baru dibandingkan dengan 3.892 run baseline historis. '
         'Semua empat kombinasi memakai 973 pair yang sama (873 MAL sumber + 100 TYP). '
         'Prompt, parser, model, dan parameter lainnya dipertahankan.', '',
         '| Model | Konfigurasi | Recall sumber 512 → 2048 | FPR TYP 512 → 2048 | JSON valid 512 → 2048 | Terpotong 512 → 2048 |',
         '|---|---|---:|---:|---:|---:|']
for group in groups:
    a, b = group['baseline'], group['candidate']
    recall = [100 * g['mal_source_recall_proxy']['rate'] for g in [a, b]]
    fpr = [100 * g['typ_assumed_benign_fpr']['rate'] for g in [a, b]]
    valid = [100 * g['json_valid'] / 973 for g in [a, b]]
    lines.append(f"| {group['model'].split('/')[-1]} | {group['config']} | "
                 f"{recall[0]:.2f}% → {recall[1]:.2f}% | {fpr[0]:.2f}% → {fpr[1]:.2f}% | "
                 f"{valid[0]:.2f}% → {valid[1]:.2f}% | {a['length_limited']} → {b['length_limited']} |")
lines.extend(['', 'Invalid tetap dihitung benign; analisis sensitivitas, macro recall kampanye, '
              'transisi valid/invalid/verdict, token, dan latency tersedia di `comparison.json`. '
              'Data ini sudah dipakai untuk menemukan masalah awal sehingga hasilnya eksploratif, '
              'bukan validasi pada holdout atau pembuktian hipotesis utama.', '',
              'Kontrol 512 token berasal dari sesi sebelumnya, bukan run bersamaan. Versi '
              'perangkat lunak dan masukan dicocokkan. Kesamaan respons lengkap/prefix '
              'dicatat sebagai diagnosis reproduksibilitas; kesamaan tersebut tidak dipaksakan. '
              'Latency antar-sesi tidak cukup untuk klaim kausal atau benchmark RQ4.', '',
              'Tidak ada evaluasi HN/retrieval, gold manusia, atau perubahan instruksi format. '
              'Korpus memiliki 224 klaster MAL; yang terbesar mencakup 607/873 pair.'])
(HERE / 'comparison.md').write_text('\n'.join(lines) + '\n')
with (HERE / 'comparison.csv').open('w', newline='') as stream:
    fields = ['model', 'config', 'max_tokens', 'completed', 'json_valid', 'length_limited',
              'mal_source_recall_proxy', 'typ_assumed_benign_fpr', 'median_latency_ms', 'p95_latency_ms']
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
    writer.writeheader()
    for group in groups:
        for label, budget in [('baseline', 512), ('candidate', 2048)]:
            g = group[label]
            writer.writerow({'model': g['model'], 'config': g['config'], 'max_tokens': budget,
                             **{k: g[k] for k in ['completed', 'json_valid', 'length_limited']},
                             **{k: g[k]['rate'] for k in ['mal_source_recall_proxy', 'typ_assumed_benign_fpr']},
                             **{k: g['cost'][k] for k in ['median_latency_ms', 'p95_latency_ms']}})
print(json.dumps({'complete': True, 'baseline_runs': 3892, 'new_runs': 3892}), flush=True)
