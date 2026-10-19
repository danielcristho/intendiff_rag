"""Compare the two larger models with the frozen 2048-token historical controls."""
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

from prompts import build

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
protocol = json.loads((HERE / 'protocol.json').read_text())
BASE = ROOT / protocol['baseline_directory']
summaries = [json.loads((folder / 'summary.json').read_text()) for folder in [BASE, HERE]]
assert all(s['complete'] and s['unique_runs'] == 3892 for s in summaries)
sources = [list(map(json.loads, (folder / 'results.jsonl').open())) for folder in [BASE, HERE]]
assert all(len(rows) == 3892 for rows in sources)
rows = sources[0] + sources[1]
assert len({r['run_key'] for r in rows}) == 7784 and not any(r.get('error') for r in rows)
pairs = {p['id']: p for p in map(json.loads, (HERE / 'pairs.jsonl').open())}
audited = {(r['model'], r['config'], r['pair_id']): r
           for r in map(json.loads, (HERE / 'context-audit.jsonl').open())}
for row in sources[1]:
    expected = audited[row['model'], row['config'], row['pair_id']]
    assert row['max_tokens'] == 2048 and row['experiment_id'] == protocol['experiment_id']
    assert row['prompt_tokens'] == expected['prompt_tokens']
    assert row['prompt_messages_sha256'] == expected['prompt_messages_sha256']
    assert row['chat_template_kwargs'] == expected['chat_template_kwargs']
    assert 0 < row['completion_tokens'] <= 2048 and row['prompt_tokens'] + 2048 <= 32768
groups = summaries[0]['groups'] + summaries[1]['groups']
indexed = {(r['model'], r['config'], r['pair_id']): r for r in rows}
for group in groups:
    selected = [r for r in rows if (r['model'], r['config']) == (group['model'], group['config'])]
    assert len(selected) == 973 and {r['pair_id'] for r in selected} == pairs.keys()
    assert sum(r['json_valid'] for r in selected) == group['json_valid']
    for subset, metric in [('MAL', 'mal_source_recall_proxy'), ('TYP', 'typ_assumed_benign_fpr')]:
        selected_subset = [r for r in selected if pairs[r['pair_id']]['subset'] == subset]
        assert group[metric]['n'] == len(selected_subset)
        assert group[metric]['positive'] == sum(r['json_valid'] and r['verdict'] == 'malicious'
                                               for r in selected_subset)


def state(row):
    return row['verdict'] if row['json_valid'] else 'invalid'


comparisons = []
for larger in protocol['models']:
    smaller_id = larger['comparison_model']
    for config in protocol['configs']:
        old_group = next(g for g in groups if (g['model'], g['config']) == (smaller_id, config))
        new_group = next(g for g in groups if (g['model'], g['config']) == (larger['id'], config))
        paired = [(indexed[smaller_id, config, pair_id], indexed[larger['id'], config, pair_id])
                  for pair_id in pairs]
        for a, b in paired:
            for field in ['config', 'pair_id', 'seed', 'temperature', 'top_p', 'top_k', 'max_tokens',
                          'label', 'truncated', 'cards', 'diff_sha256', 'evaluation_scope',
                          'label_origin', 'human_annotation_verified']:
                assert a[field] == b[field], (field, b['pair_id'])
            messages = build(config, pairs[b['pair_id']])
            assert hashlib.sha256(json.dumps(messages).encode()).hexdigest() == b['prompt_messages_sha256']
        comparisons.append({'smaller_model': smaller_id, 'larger_model': larger['id'], 'config': config,
                            'paired_transitions': {subset: dict(Counter(f'{state(a)}->{state(b)}'
                                 for a, b in paired if pairs[b['pair_id']]['subset'] == subset))
                                 for subset in ['MAL', 'TYP']},
                            'delta_percentage_points': {metric: 100 * (new_group[metric]['rate']
                                  - old_group[metric]['rate']) for metric in
                                  ['mal_source_recall_proxy', 'typ_assumed_benign_fpr']}})
result = {'complete': True, 'experiment_id': protocol['experiment_id'], 'new_runs': 3892,
          'historical_runs': 3892, 'combined_runs': 7784, 'historical_control': True,
          'human_annotation_verified': False, 'groups': groups, 'comparisons': comparisons}
(HERE / 'comparison.json').write_text(json.dumps(result, indent=2) + '\n')
(HERE / 'results.all-models.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows))
lines = ['# Pembanding model 3–4B versus 7–8B', '',
         'Lengkap: 3.892 inferensi baru + 3.892 respons kontrol historis D82. Semua model memakai '
         '973 pair yang sama, output 2.048 token, BF16, dan konteks 32.768. '
         'Label sumber; bukan evaluasi gold atau uji hipotesis konfirmatori.', '',
         '| Model | Konfigurasi | Recall MAL sumber | FPR TYP | JSON valid | Terpotong | Macro recall kampanye |',
         '|---|---|---:|---:|---:|---:|---:|']
for g in groups:
    lines.append(f"| {g['model'].split('/')[-1]} | {g['config']} | "
                 f"{100*g['mal_source_recall_proxy']['rate']:.2f}% | "
                 f"{100*g['typ_assumed_benign_fpr']['rate']:.2f}% | "
                 f"{100*g['json_valid']/973:.2f}% | {g['length_limited']} | "
                 f"{100*g['mal_campaign_macro_recall_proxy']:.2f}% |")
lines.extend(['', 'Denominator per baris: 873 MAL, 100 TYP, dan 973 respons. Invalid dihitung benign; '
              'sensitivitas invalid-as-malicious dan biaya ada di comparison.json.', '',
              'Qwen2.5-Coder dibandingkan dalam seri yang sama. Qwen3-4B-Instruct-2507 dan '
              'Qwen3-8B juga berbeda checkpoint/post-training, sehingga hasil tidak mengisolasi '
              'efek ukuran. Qwen3-8B memakai hard switch non-thinking; prompt dan parser dipertahankan.', '',
              'Alokasi GPU 0,65 pada kontrol historis dan 0,80 pada model baru. Latency antar-sesi '
              'bukan estimasi kausal efek ukuran. Tidak ada gold manusia, HN, RAG, atau pembekuan G1/G2. '
              'Hasil tetap eksploratif; kelompok ukuran tidak mewakili seluruh populasi model.'])
(HERE / 'comparison.md').write_text('\n'.join(lines) + '\n')
with (HERE / 'comparison.csv').open('w', newline='') as stream:
    fields = ['model', 'config', 'completed', 'json_valid', 'length_limited', 'recall', 'fpr',
              'macro_recall', 'median_latency_ms', 'p95_latency_ms']
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
    writer.writeheader()
    for g in groups:
        writer.writerow({**{k: g[k] for k in fields[:5]},
                         'recall': g['mal_source_recall_proxy']['rate'],
                         'fpr': g['typ_assumed_benign_fpr']['rate'],
                         'macro_recall': g['mal_campaign_macro_recall_proxy'],
                         **{k: g['cost'][k] for k in fields[-2:]}})
print(json.dumps({'complete': True, 'new_runs': 3892, 'combined_runs': 7784}), flush=True)
