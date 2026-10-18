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
    # Indonesian manuscript: decimal comma, thousands dot.
    def num(value, digits=2, sign=''):
        return f'{value:{sign},.{digits}f}'.replace(',', '_').replace('.', ',').replace('_', '.')
    def pct(value):
        return num(value * 100)
    def signed(value):
        return num(value, sign='+').replace('-', '$-$')
    contrasts = (('DIFF+I', 'Tambah M'), ('DIFF+I+MM', 'MM ke MB'), ('DIFF+MB', 'Tambah intent'))
    rows, all_rows, cost, sensitivity, contrast_rows, delta_rows = [], [], [], [], [], []
    for tag, name in names.items():
        for config in ('DIFF', 'DIFF+I'):
            r = get(tag, config)
            rows.append(f"{name} & {config} & {r['old_tp'] + r['new_tp']}/129 & "
                        f"{pct(r['tpr'])} [{pct(r['tpr_low'])}; {pct(r['tpr_high'])}] & "
                        f"{num(r['typ_fp'], 0)}/1.868 & {pct(r['fpr'])} [{pct(r['fpr_low'])}; {pct(r['fpr_high'])}]")
        for config in ('DIFF', 'DIFF+I', 'DIFF+I+M', 'DIFF+I+MM', 'DIFF+I+MB', 'DIFF+MB'):
            r = get(tag, config)
            all_rows.append(f"{name} & {config} & {pct(r['tpr'])} & "
                            f"{pct(r['fpr'])} & {pct(r['combined_accuracy'])} & {pct(r['combined_balanced_accuracy'])}")
        subset = [get(tag, c) for c in ('DIFF', 'DIFF+I+MM', 'DIFF+I+MB')]
        delta_rows.append(f"{name} & " + ' & '.join(pct(r['tp_with_delta'] / 42) for r in subset) + ' & '
                          + ' & '.join(pct(r['tp_empty_delta'] / 87) for r in subset))
        a, b = get(tag, 'DIFF'), get(tag, 'DIFF+I+MB')
        cost.append(f"{name} & {num(a['mean_prompt_tokens'], 0)} / {num(b['mean_prompt_tokens'], 0)} & "
                    f"{num(a['median_latency_ms']/1000, 3)} / {num(b['median_latency_ms']/1000, 3)} & "
                    f"{num(a['p95_latency_ms']/1000, 3)} / {num(b['p95_latency_ms']/1000, 3)}")
        c = get(tag, 'DIFF+I+MB', 'malicious')
        json_valid = (b['old_json_validity'] * 11406 + b['new_json_validity'] * 576) / 11982
        sensitivity.append(f"{name} & {pct(json_valid)} & "
                           f"{pct(b['tpr'])} / {pct(c['tpr'])} & {pct(b['fpr'])} / {pct(c['fpr'])}")
        for baseline, label in contrasts:
            e = next(e for e in effects if e['tag'] == tag and e['baseline'] == baseline)
            lo, hi = e['pooled_campaign_bootstrap_95']
            flo, fhi = e['fpr_campaign_bootstrap_95']
            contrast_rows.append(f"{name if baseline == 'DIFF+I' else ''} & {label} & "
                                 f"{signed(e['pooled_delta_points'])} [{signed(lo)}; {signed(hi)}] & "
                                 f"{signed(e['fpr_delta_points'])} [{signed(flo)}; {signed(fhi)}]")
    table('main-results.tex',
          'Kemampuan dasar tanpa contoh rujukan: smart-diff saja (DIFF) dan smart-diff dengan intent (DIFF+I). '
          'TPR memakai 129 MAL dari 98 kampanye; FPR memakai 1.868 TYP. CI 95\\% dihitung dengan bootstrap '
          'per klaster kampanye. Invalid dianggap benign.',
          'tab:main', 'llrrrr', 'Model & Konfigurasi & TP & TPR (\\%) [CI] & FP & FPR (\\%) [CI]', rows)
    table('full-results.tex',
          'Seluruh konfigurasi, dalam persen. TPR memakai 129 MAL; FPR memakai 1.868 TYP. '
          'Akurasi dan BA memakai keduanya dan bersifat deskriptif. BA: balanced accuracy.',
          'tab:full', 'llrrrr', 'Model & Konfigurasi & TPR & FPR TYP & Akurasi & BA', all_rows)
    table('mb-contrast.tex',
          'Kontras berpasangan untuk contoh rujukan dan intent, dalam poin persentase. Tambah M: DIFF+I ke DIFF+I+M; '
          'MM ke MB: DIFF+I+MM ke DIFF+I+MB; tambah intent: DIFF+MB ke DIFF+I+MB. CI 95\\% dihitung dengan '
          'bootstrap berpasangan per klaster kampanye pada 129 MAL (98 klaster) dan 1.868 TYP.',
          'tab:contrast', 'llrr', 'Model & Kontras & $\\Delta$TPR [CI 95\\%] & $\\Delta$FPR [CI 95\\%]', contrast_rows)
    table('cost.tex',
          'Biaya permintaan pada 1.901 pasangan dari sesi inferensi yang sama. Setiap sel menunjukkan DIFF / DIFF+I+MB. '
          'Latensi dalam detik, setelah warm-up, dengan prefix caching; tidak mencakup preprocessing atau startup.',
          'tab:cost', 'lrrr', 'Model & Token input rata-rata & Latensi median & Latensi p95', cost)
    table('sensitivity.tex',
          'Validitas JSON pada 11.982 respons test per model dan sensitivitas DIFF+I+MB. '
          'Dua angka pada kolom TPR/FPR menghitung invalid sebagai benign/malicious; TPR memakai 129 MAL. Semuanya dalam persen.',
          'tab:sensitivity', 'lrrr', 'Model & JSON valid & TPR & FPR TYP', sensitivity)
    table('delta-subsets.tex',
          'TPR menurut ada atau tidaknya perubahan kemampuan pada MAL, dalam persen. Pada 87 MAL tanpa perubahan '
          'kemampuan, semua contoh berskor nol dan contoh dipilih oleh pemecah seri berbasis hash. Invalid dianggap benign.',
          'tab:delta', 'lrrrrrr', 'Model & \\multicolumn{3}{c}{Ada perubahan (42)} & \\multicolumn{3}{c}{Tanpa perubahan (87)} \\\\\n'
          ' & DIFF & MM & MB & DIFF & MM & MB', delta_rows)
    render_paired_effects(effects, names)


def render_paired_effects(effects, names):
    """Render the English figure independently of the manuscript tables."""
    plt.rcParams['pdf.fonttype'] = 42
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 3.45), sharey=True)
    baselines = ('DIFF+I', 'DIFF+I+MM', 'DIFF+MB')
    titles = ('(a) Add a malicious example\nDIFF+I → DIFF+I+M',
              '(b) Replace MM with MB\nDIFF+I+MM → DIFF+I+MB',
              '(c) Add intent to MB\nDIFF+MB → DIFF+I+MB')
    for axis, baseline, title in zip(axes, baselines, titles):
        rows = [next(e for e in effects if e['tag'] == tag and e['baseline'] == baseline) for tag in names]
        for i, e in enumerate(rows):
            lo, hi = e['pooled_campaign_bootstrap_95']; point = e['pooled_delta_points']
            axis.errorbar(point, i, xerr=[[point-lo], [hi-point]], fmt='o', markersize=3,
                          capsize=2, color='#17638a', linewidth=1)
        axis.axvline(0, color='0.55', linestyle='--', linewidth=.7)
        axis.set_title(title, fontsize=8); axis.set_xlim(-25, 32)
        axis.set_xlabel('Change in TPR (percentage points)', fontsize=7)
        axis.tick_params(labelsize=7); axis.grid(axis='x', alpha=.18)
        axis.spines[['top', 'right']].set_visible(False)
    axes[0].set_yticks(range(len(names)), names.values(), fontsize=7)
    axes[0].invert_yaxis()
    fig.tight_layout(pad=.6, rect=(0, .17, 1, 1))
    fig.text(.5, .09, 'Point: paired estimate; bar: 95% campaign-cluster bootstrap interval; dashed line: no change.',
             ha='center', fontsize=7)
    fig.text(.5, .035, 'TPR: true positive rate; I: package intent; M: malicious example; B: benign example. 129 malicious updates.',
             ha='center', fontsize=7)
    figures = Path('labs/latex/figures'); figures.mkdir(exist_ok=True)
    fig.savefig(figures / 'paired-effects.pdf', bbox_inches='tight')
    fig.savefig(figures / 'paired-effects.png', dpi=300, bbox_inches='tight')
    fig.savefig(figures / 'paired-effects.tiff', dpi=1000, bbox_inches='tight',
                pil_kwargs={'compression': 'tiff_lzw'})
    plt.close(fig)
