"""Usage: python pipeline/sampling_plots.py --release DIR (after sampling_report.py)."""
import argparse
import csv
import statistics
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402

from configs import CONFIGS, CONTRASTS  # noqa: E402

INK, MUTED, GRID = '#1f1f1f', '#6b6b6b', '#e4e4e4'
# CONFIG_STYLE pairs each hue with a marker: three hues sit below 3:1 contrast and
# yellow/aqua are close under tritanopia, so colour never carries identity alone.
CONFIG_STYLE = dict(zip(CONFIGS, zip(('#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300'),
                                     ('o', 's', '^', 'D', 'v', 'P'))))
MODEL_STYLE = {'qwen3': ('Qwen3-4B', '#2a78d6', 'o'), 'qwen25': ('Qwen2.5-3B', '#eb6834', 's')}
CONTRAST_TITLES = ('Add a malicious example', 'Replace MM with MB', 'Add intent to MB')


def read(release, name):
    with (release / name).open() as stream:
        rows = list(csv.DictReader(stream))
    for row in rows:
        row.update({k: float(v) for k, v in row.items() if k not in ('model', 'config', 'baseline', 'variant')
                    and v not in ('True', 'False')})
    return rows


def style(axis, title=None):
    if title:
        axis.set_title(title, fontsize=8, color=INK, loc='left')
    axis.tick_params(labelsize=7, colors=INK)
    axis.grid(axis='y', color=GRID, lw=.7)
    axis.set_axisbelow(True)
    axis.spines[['top', 'right']].set_visible(False)
    axis.spines[['left', 'bottom']].set_color(MUTED)


def save(fig, out, name):
    fig.savefig(out / f'{name}.pdf', bbox_inches='tight')
    fig.savefig(out / f'{name}.png', dpi=300, bbox_inches='tight')
    plt.close(fig)


def rates(metrics, temperatures, out):
    # A shared y per row keeps Qwen3's ±2-point drift from looking as steep as Qwen2.5's slide.
    fig, axes = plt.subplots(2, 2, figsize=(7.2, 5.4), sharey='row')
    for col, tag in enumerate(MODEL_STYLE):
        for row, rate in enumerate(('tpr', 'fpr')):
            axis = axes[row, col]
            for config, (colour, marker) in CONFIG_STYLE.items():
                seeds = [[m[rate] * 100 for m in metrics if (m['model'], m['config'], m['temperature']) ==
                          (tag, config, t)] for t in temperatures]
                mean = [statistics.fmean(s) for s in seeds]
                # Bars span the three seeds; at T=0 they collapse to the point.
                # max(0, ...): identical seeds leave a -1e-17 rounding residue that errorbar rejects.
                spread = [[max(0, m - min(s)) for m, s in zip(mean, seeds)],
                          [max(0, max(s) - m) for m, s in zip(mean, seeds)]]
                axis.errorbar(temperatures, mean, yerr=spread, color=colour, marker=marker, markersize=4,
                              lw=1.4, elinewidth=.8, capsize=2, label=config)
            style(axis, f'{MODEL_STYLE[tag][0]}: {rate.upper()}')
            axis.set_xticks(temperatures)
            axis.set_ylabel(f'{rate.upper()} (%)', fontsize=7, color=INK)
    for axis in axes[1]:
        axis.set_xlabel('Temperature', fontsize=7, color=INK)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='upper center', ncol=6, fontsize=7, frameon=False)
    fig.tight_layout(rect=(0, .03, 1, .95))
    fig.text(.5, .005, 'Point: mean of seeds 0, 1, 2; bar: seed minimum to maximum. TPR on 129 MAL, FPR on 1,868 TYP.',
             ha='center', fontsize=6.5, color=MUTED)
    save(fig, out, 'sampling-rates')


def flips(stability, temperatures, out):
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.8), sharey=True)
    for axis, (key, title) in zip(axes, (('flip_all', 'All 1,997 pairs'), ('flip_mal', '129 MAL pairs'))):
        for tag, (name, colour, marker) in MODEL_STYLE.items():
            per_t = [[s[key] * 100 for s in stability if (s['model'], s['temperature']) == (tag, t)]
                     for t in temperatures]
            axis.fill_between(temperatures, [min(v) for v in per_t], [max(v) for v in per_t], color=colour,
                              alpha=.18, lw=0)
            axis.plot(temperatures, [statistics.fmean(v) for v in per_t], color=colour, marker=marker,
                      markersize=4, lw=1.6, label=name)
        style(axis, title)
        axis.set_xticks(temperatures)
        axis.set_xlabel('Temperature', fontsize=7, color=INK)
    axes[0].set_ylabel('Pairs whose verdict differs across seeds (%)', fontsize=7, color=INK)
    axes[0].legend(fontsize=7, frameon=False, loc='upper left')
    fig.tight_layout(rect=(0, .06, 1, 1))
    fig.text(.5, .005, 'Line: mean over the six configurations; band: configuration minimum to maximum.',
             ha='center', fontsize=6.5, color=MUTED)
    save(fig, out, 'sampling-flips')


def contrasts(rows, temperatures, out):
    fig, axes = plt.subplots(2, 3, figsize=(7.2, 4.6), sharex=True)
    offsets = {'qwen3': -.045, 'qwen25': .045}
    for col, ((baseline, variant), title) in enumerate(zip(CONTRASTS, CONTRAST_TITLES)):
        for row, rate in enumerate(('tpr', 'fpr')):
            axis = axes[row, col]
            axis.axhline(0, color=MUTED, ls='--', lw=.7)
            for tag, (name, colour, marker) in MODEL_STYLE.items():
                cells = [c for c in rows if (c['model'], c['baseline'], c['variant']) == (tag, baseline, variant)]
                for c in cells:
                    # Seeds sit side by side inside each temperature so their intervals stay legible.
                    x = c['temperature'] + offsets[tag] + (c['seed'] - 1) * .025
                    point = c[f'{rate}_delta_points']
                    axis.errorbar(x, point, yerr=[[point - c[f'{rate}_low']], [c[f'{rate}_high'] - point]],
                                  color=colour, marker=marker, markersize=3, lw=.8, capsize=1.2,
                                  label=name if c is cells[0] else None)
            style(axis, f'{title}\n{baseline} → {variant}' if row == 0 else None)
            axis.set_xticks(temperatures)
            if col == 0:
                axis.set_ylabel(f'Δ{rate.upper()} (percentage points)', fontsize=7, color=INK)
    for axis in axes[1]:
        axis.set_xlabel('Temperature', fontsize=7, color=INK)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='upper center', ncol=2, fontsize=7, frameon=False)
    fig.tight_layout(rect=(0, .03, 1, .95))
    fig.text(.5, .005, 'Point: paired estimate per seed (0, 1, 2 left to right); bar: 95% campaign-cluster bootstrap '
             'interval; dashed line: no change.', ha='center', fontsize=6.5, color=MUTED)
    save(fig, out, 'sampling-contrasts')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--release', type=Path, required=True)
    release = parser.parse_args().release
    out = release / 'figures'
    out.mkdir(exist_ok=True)
    plt.rcParams['pdf.fonttype'] = 42
    metrics = read(release, 'metrics.csv')
    temperatures = sorted({m['temperature'] for m in metrics})
    rates(metrics, temperatures, out)
    flips(read(release, 'stability.csv'), temperatures, out)
    contrasts(read(release, 'contrasts.csv'), temperatures, out)
    print(f'wrote {out}')


if __name__ == '__main__':
    main()
