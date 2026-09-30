"""Export all eight completed groups without selecting favorable results."""
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'data/evaluation/model-families-20261001'
data = json.loads((HERE / 'comparison.json').read_text())
assert data['complete'] and data['combined_runs'] == 11676
models = [('Qwen/Qwen2.5-Coder-3B-Instruct', 'Qwen2.5-Coder\n3.09B (historis)'),
          ('Qwen/Qwen3-4B-Instruct-2507', 'Qwen3-2507\n4.0B (historis)'),
          ('microsoft/Phi-4-mini-instruct', 'Phi-4-mini\n3.836B'),
          ('Qwen/Qwen2.5-Coder-7B-Instruct', 'Qwen2.5-Coder\n7.61B (historis)'),
          ('Qwen/Qwen3-8B', 'Qwen3\n8.2B (historis)'),
          ('meta-llama/Llama-3.1-8B-Instruct', 'Llama-3.1\n8.030B')]

groups = {(g['model'], g['config']): g for g in data['groups']}
fig, axes = plt.subplots(1, 3, figsize=(18, 5), sharey=True)
metrics = [('Recall label sumber MAL', 'mal_source_recall_proxy'),
           ('FPR TYP (lebih rendah lebih baik)', 'typ_assumed_benign_fpr'),
           ('JSON valid', 'json_valid')]
x = np.arange(6)
for ax, (title, metric) in zip(axes, metrics):
    for config, shift, color in [('DIFF', -.2, '#64748b'), ('DIFF+I', .2, '#007e87')]:
        selected = [groups[m, config] for m, _ in models]
        values = [100 * (g[metric] / g['completed'] if metric == 'json_valid'
                         else g[metric]['rate']) for g in selected]
        bars = ax.bar(x + shift, values, width=.38, label=config, color=color)
        ax.bar_label(bars, fmt='%.1f', fontsize=8, padding=3)
    ax.set_title(title, fontsize=10)
    ax.set_xticks(x, [label for _, label in models], fontsize=8)
    ax.set_ylim(0, 112)
    ax.set_yticks(range(0, 101, 20))
    ax.grid(axis='y', alpha=.18)
    ax.set_axisbelow(True)
    ax.spines[['top', 'right']].set_visible(False)
axes[0].set_ylabel('Persen (%)')
axes[0].legend(loc='upper left', bbox_to_anchor=(0, -.19), ncol=2, frameon=False)
fig.suptitle('Enam model lokal: Qwen, Phi, Llama — output 2.048 token', fontsize=14)
fig.text(.5, .025, '973 pair per konfigurasi; label sumber, belum gold manusia. Invalid dihitung benign.\n'
         'Kontrol historis; keluarga, pelatihan, dan template berbeda. Hasil eksploratif, bukan efek kausal ukuran.',
         ha='center', fontsize=9)
fig.tight_layout(rect=(0, .12, 1, .95))
for extension in ['png', 'pdf']:
    fig.savefig(HERE / f'comparison.{extension}', dpi=200, bbox_inches='tight')
plt.close(fig)
