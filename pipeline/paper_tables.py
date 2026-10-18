"""Render manuscript tables and a paired-effect plot from audited numeric records."""
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT = Path('labs/latex/generated')


def table(name, caption, label, columns, header, rows, wide=True):
    environment = 'table*' if wide else 'table'
    lines = [f'\\begin{{{environment}}}[t]', '\\centering\\small', f'\\caption{{{caption}}}',
             f'\\label{{{label}}}', f'\\begin{{tabular}}{{{columns}}}', '\\toprule',
             header + r' \\', '\\midrule', *[r + r' \\' for r in rows],
             '\\bottomrule', '\\end{tabular}', f'\\end{{{environment}}}', '']
    (OUT / name).write_text('\n'.join(lines))


def render(records, effects, names):
    OUT.mkdir(parents=True, exist_ok=True)
    selected = {(r['tag'], r['config'], r['invalid_as']): r for r in records}
    def get(tag, config, policy='benign'):
        return selected[tag, config, policy]
    def pct(value):
        return f'{value*100:.2f}'
    rows, all_rows, cost, sensitivity, contrast_rows = [], [], [], [], []
    for tag, name in names.items():
        for config in ('DIFF', 'DIFF+I+MB'):
            r = get(tag, config)
            rows.append(f"{name} & {config} & {r['old_tp']}/33 & {r['new_tp']}/96 & "
                        f"{pct(r['new_tpr'])} [{pct(r['new_tpr_low'])}, {pct(r['new_tpr_high'])}] & "
                        f"{r['typ_fp']}/1868 ({pct(r['fpr'])})")
        for config in ('DIFF', 'DIFF+I', 'DIFF+I+M', 'DIFF+I+MM', 'DIFF+I+MB', 'DIFF+MB'):
            r = get(tag, config)
            all_rows.append(f"{name} & {config} & {pct(r['old_tpr'])} & {pct(r['new_tpr'])} & "
                            f"{pct(r['fpr'])} & {pct(r['combined_accuracy'])} & {pct(r['combined_balanced_accuracy'])}")
        a, b = get(tag, 'DIFF'), get(tag, 'DIFF+I+MB')
        cost.append(f"{name} & {a['mean_prompt_tokens']:.0f} / {b['mean_prompt_tokens']:.0f} & "
                    f"{a['median_latency_ms']/1000:.3f} / {b['median_latency_ms']/1000:.3f} & "
                    f"{a['p95_latency_ms']/1000:.3f} / {b['p95_latency_ms']/1000:.3f}")
        c = get(tag, 'DIFF+I+MB', 'malicious')
        sensitivity.append(f"{name} & {pct(b['old_json_validity'])} / {pct(b['new_json_validity'])} & "
                           f"{pct(b['new_tpr'])} / {pct(c['new_tpr'])} & {pct(b['fpr'])} / {pct(c['fpr'])}")
        e = next(e for e in effects if e['tag'] == tag and e['baseline'] == 'DIFF+I+MM')
        lo, hi = e['campaign_bootstrap_95']
        contrast_rows.append(f"{name} & {e['delta_points']:+.2f} [{lo:+.2f}, {hi:+.2f}] & {e['fpr_delta_points']:+.2f}")
    table('main-results.tex',
          'Deteksi tanpa konteks tambahan (DIFF) dan dengan intent serta contoh M/B. '
          'TPR tambahan dan CI 95\\% bootstrap kampanye memakai 96 MAL; FP memakai 1.868 TYP pada evaluasi awal. '
          'Kolom terakhir memuat hitungan dan persentase. Invalid dianggap benign.',
          'tab:main', 'llrrrr', 'Model & Konfigurasi & TP awal & TP tambahan & TPR tambahan (\\%) & FP TYP (\\%)', rows)
    table('full-results.tex',
          'Seluruh konfigurasi, dalam persen. Akurasi dan BA gabungan memakai 129 MAL + 1.868 TYP dan bersifat deskriptif; '
          'TYP tidak dievaluasi ulang pada batch tambahan. BA: balanced accuracy.',
          'tab:full', 'llrrrrr', 'Model & Konfigurasi & TPR awal & TPR tambahan & FPR TYP & Akurasi gab. & BA gab.', all_rows)
    table('mb-contrast.tex',
          'Mengganti contoh kedua dari malicious menjadi benign (DIFF+I+MB dikurangi DIFF+I+MM). '
          'Selisih dalam poin persentase; CI 95\\% berkelompok memakai 65 kampanye MAL tambahan. '
          'Selisih FPR adalah estimasi titik pada TYP awal.',
          'tab:contrast', 'lrr', 'Model & $\\Delta$TPR tambahan [CI95\\%] & $\\Delta$FPR TYP', contrast_rows)
    table('cost.tex',
          'Biaya permintaan pada 1.901 pasangan evaluasi awal. Setiap sel menunjukkan DIFF / DIFF+I+MB. '
          'Latensi dalam detik, setelah warm-up, dengan prefix caching; tidak mencakup preprocessing atau startup.',
          'tab:cost', 'lrrr', 'Model & Token input rata-rata & Latensi median & Latensi p95', cost)
    table('sensitivity.tex',
          'Validitas JSON seluruh konfigurasi (awal/tambahan) dan sensitivitas DIFF+I+MB. '
          'Dua angka pada kolom TPR/FPR menghitung invalid sebagai benign/malicious; semuanya dalam persen.',
          'tab:sensitivity', 'lrrr', 'Model & JSON valid awal/tambahan & TPR tambahan & FPR TYP', sensitivity)
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.75), sharey=True)
    baselines = ('DIFF+I', 'DIFF+I+MM', 'DIFF+MB')
    titles = ('Tambah contoh M', 'Ganti MM dengan MB', 'Tambah intent pada MB')
    for axis, baseline, title in zip(axes, baselines, titles):
        rows = [next(e for e in effects if e['tag'] == tag and e['baseline'] == baseline) for tag in names]
        for i, e in enumerate(rows):
            lo, hi = e['campaign_bootstrap_95']; point = e['delta_points']
            axis.errorbar(point, i, xerr=[[point-lo], [hi-point]], fmt='o', markersize=3,
                          capsize=2, color='#17638a', linewidth=1)
        axis.axvline(0, color='0.55', linestyle='--', linewidth=.7)
        axis.set_title(title, fontsize=8); axis.set_xlim(-25, 32)
        axis.set_xlabel('Selisih TPR (poin persentase)', fontsize=7)
        axis.tick_params(labelsize=7); axis.grid(axis='x', alpha=.18)
        axis.spines[['top', 'right']].set_visible(False)
    axes[0].set_yticks(range(len(names)), names.values(), fontsize=7)
    axes[0].invert_yaxis()
    fig.tight_layout(pad=.6)
    figures = Path('labs/latex/figures'); figures.mkdir(exist_ok=True)
    fig.savefig(figures / 'paired-effects.pdf', bbox_inches='tight')
    fig.savefig(figures / 'paired-effects.png', dpi=200, bbox_inches='tight')
    plt.close(fig)
