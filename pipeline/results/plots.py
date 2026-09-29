"""Figures for the result tables."""
import argparse
from pathlib import Path

from pipeline.results.comparisons import COMPARISONS, RECALL_GUARD
from pipeline.results.figure_style import (BLUE, GREEN, GREY, PANELS, STYLE, WHISKER, bounds, configs_of,
                                           legend, plt, save, short_model, wrap_label)
from pipeline.results.pareto import pareto_front
from pipeline.results.report import add_source_arguments, load_reports
from pipeline.shared.config import layout

# plot_rates draws one panel per metric, grouped by configuration and model.
def plot_rates(reports, stem):
    configs = configs_of(reports)
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.6))
    width = 0.8 / len(reports)
    for panel, (ax, (key, title)) in enumerate(zip(axes, PANELS)):
        for index, (entry, colour) in enumerate(zip(reports, (GREY, BLUE))):
            x = [i + (index - 0.5 * (len(reports) - 1)) * width for i in range(len(configs))]
            values, lows, highs = [], [], []
            for config in configs:
                cell = entry["descriptive"].get(config) or {}
                low, high = bounds(cell.get(key), cell.get(f"{key}_n", 0))
                values.append((cell.get(key) or 0.0) * 100)
                lows.append(low)
                highs.append(high)
            # The edge keeps a 0% bar visible, or an all-zero panel reads as missing data.
            ax.bar(x, values, width, color=colour, edgecolor=colour, linewidth=0.8,
                   label=short_model(entry["model"]))
            # The interval keeps four pairs at 100% from looking like a finding.
            ax.errorbar(x, values, yerr=[lows, highs], fmt="none",
                        ecolor=WHISKER[colour], elinewidth=0.7, capsize=1.6)
        ax.set_title(f"({chr(97 + panel)}) {title} (%)", loc="left")
        ax.set_xticks(range(len(configs)))
        ax.set_xticklabels([wrap_label(config) for config in configs])
        ax.set_ylim(0, 105)
    legend(fig, axes[0].get_legend_handles_labels()[0])
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    save(fig, stem)


# plot_comparisons draws how each comparison moved the false positive rate and its recall cost, per model.
def plot_comparisons(reports, stem):
    fig, axes = plt.subplots(2, len(reports), figsize=(3.6 * len(reports), 4.2),
                             squeeze=False, sharey="row")
    width = 0.36
    for column, entry in enumerate(reports):
        tests = entry["tests"]
        top, bottom = axes[0][column], axes[1][column]
        for index, (key, colour, label) in enumerate((("fpr_baseline", GREY, "Baseline"),
                                                      ("fpr_variant", BLUE, "Variant"))):
            x = [i + (index - 0.5) * width for i in range(len(tests))]
            top.bar(x, [(test[key] or 0.0) * 100 for test in tests], width,
                    color=colour, edgecolor=colour, linewidth=0.8, label=label)
        top.set_title(f"({chr(97 + column)}) {short_model(entry['model'])}", loc="left")
        top.set_ylim(0, 105)
        top.set_xticks(range(len(tests)))
        top.set_xticklabels([test["comparison"] for test in tests])

        for index, test in enumerate(tests):
            delta, (low, high) = test["recall_delta_pt"], test["recall_ci_pt"]
            # A hollow marker shows a comparison the recall guard does not gate.
            gated = COMPARISONS[test["comparison"]]["recall_guard"]
            bottom.errorbar([index], [delta], yerr=[[delta - low], [high - delta]],
                            fmt="o", ms=3.6, color=GREEN, mfc=GREEN if gated else "white",
                            mew=0.9, ecolor="0.35", elinewidth=0.8, capsize=2)
        bottom.axhline(0, color="0.8", lw=0.6)
        bottom.axhline(RECALL_GUARD, color="0.2", lw=0.9, ls=(0, (4, 2)),
                       label=f"Recall guard ({RECALL_GUARD:g} pt)")
        bottom.plot([], [], "o", ms=3.6, color=GREEN, mfc="white", mew=0.9,
                    label="Guard not applied")
        bottom.set_xticks(range(len(tests)))
        bottom.set_xticklabels([f"{t['comparison']}\n{t['baseline']}→{t['variant']}"
                                for t in tests])
    axes[0][0].set_ylabel("FPR on hard negatives (%)")
    axes[1][0].set_ylabel("Recall change (pt)")
    legend(fig, axes[0][0].get_legend_handles_labels()[0]
            + axes[1][0].get_legend_handles_labels()[0])
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    save(fig, stem)


# plot_pareto draws cost against false positives and fills the non-dominated points.
def plot_pareto(reports, stem):
    fig, axes = plt.subplots(1, len(reports), figsize=(3.6 * len(reports), 2.7),
                             squeeze=False, sharey=True)
    for column, (ax, entry) in enumerate(zip(axes[0], reports)):
        configs = sorted(entry["descriptive"])
        cells = [entry["descriptive"][config] for config in configs]
        points = [(c["median_latency_ms"] or 0.0, (c["fpr_hn"] or 0.0) * 100,
                   c["recall"] or 0.0) for c in cells]
        # Objectives: lower latency, fewer false positives, higher recall; the axes show the first two.
        front = set(pareto_front(points, (-1, -1, 1)))
        named = {}
        for index, (config, point) in enumerate(zip(configs, points)):
            on_front = index in front
            ax.plot([point[0]], [point[1]], "o", ms=5.0 if on_front else 4.0,
                    mfc=BLUE if on_front else "white", mec=BLUE if on_front else GREY,
                    mew=0.9, zorder=2 if on_front else 1)
            if on_front:
                named.setdefault(point[:2], []).append(config)
        # Only the front is labelled, since naming dominated points buries the answer.
        for (x, y), names in named.items():
            ax.annotate(", ".join(names), (x, y), fontsize=6.5, xytext=(4, 4),
                        textcoords="offset points")
        ax.set_title(f"({chr(97 + column)}) {short_model(entry['model'])}", loc="left")
        ax.set_xlabel("Median latency (ms)")
    axes[0][0].set_ylabel("FPR on hard negatives (%)")
    legend(fig, [plt.Line2D([], [], marker="o", ls="", ms=5.0, mfc=BLUE, mec=BLUE,
                             label="Pareto-optimal"),
                  plt.Line2D([], [], marker="o", ls="", ms=4.0, mfc="white", mec=GREY,
                             mew=0.9, label="Dominated")])
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    save(fig, stem)


def main(argv=None):
    data = layout()
    parser = argparse.ArgumentParser(prog="plots")
    add_source_arguments(parser, data)
    parser.add_argument("--out", default=str(data.figures))
    args = parser.parse_args(argv)
    reports = load_reports(args.results, args.pairs, args.invalid_as)
    plt.rcParams.update(STYLE)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for name, draw in (("fig_rates", plot_rates), ("fig_comparisons", plot_comparisons),
                       ("fig_pareto", plot_pareto)):
        draw(reports, out / name)
        print(out / f"{name}.pdf")
