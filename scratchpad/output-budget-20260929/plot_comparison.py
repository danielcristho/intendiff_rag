"""Export the completed output-budget comparison as PNG and PDF."""
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'data/evaluation/output-budget-20260929'
comparison = json.loads((HERE / 'comparison.json').read_text())
assert comparison['complete'] and comparison['new_runs'] == 3892
groups = comparison['groups']
labels = [f"{'Qwen2.5' if 'Qwen2.5' in g['model'] else 'Qwen3'}\n{g['config']}"
          for g in groups]
fig, axes = plt.subplots(1, 3, figsize=(13, 4.7), sharey=True)
metrics = [('Recall label sumber MAL', 'mal_source_recall_proxy'),
           ('FPR TYP (lebih rendah lebih baik)', 'typ_assumed_benign_fpr'),
           ('JSON valid', 'json_valid')]
x = np.arange(len(groups))
for ax, (title, metric) in zip(axes, metrics):
    for label, budget, shift, color in [('baseline', '512 (historis)', -.2, '#64748b'),
                                      ('candidate', '2048', .2, '#007e87')]:
        values = [100 * (g[label][metric] / g[label]['completed'] if metric == 'json_valid'
                         else g[label][metric]['rate']) for g in groups]
        bars = ax.bar(x + shift, values, width=.38, label=budget, color=color)
        ax.bar_label(bars, fmt='%.1f', fontsize=8, padding=3)
    ax.set_title(title, fontsize=10)
    ax.set_xticks(x, labels, fontsize=9)
    ax.set_ylim(0, 112)
    ax.set_yticks(range(0, 101, 20))
    ax.grid(axis='y', alpha=.18)
    ax.set_axisbelow(True)
    ax.spines[['top', 'right']].set_visible(False)
axes[0].set_ylabel('Persen (%)')
axes[0].legend(loc='upper left', bbox_to_anchor=(0, -.18), ncol=2, frameon=False)
fig.suptitle('Eksperimen batas output: 512 → 2.048 token', fontsize=14)
fig.text(.5, .02, '973 pair × 4 kombinasi; label sumber, belum gold manusia. '
         'Invalid dihitung benign. Kontrol historis; hasil eksploratif.',
         ha='center', fontsize=9)
fig.tight_layout(rect=(0, .08, 1, .95))
for extension in ['png', 'pdf']:
    fig.savefig(HERE / f'comparison.{extension}', dpi=200, bbox_inches='tight')
plt.close(fig)
