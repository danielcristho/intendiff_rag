"""Figures for the result tables.

    python pipeline/plots.py --results data/results.jsonl --pairs data/pairs.jsonl --out figures
    python pipeline/plots.py --selfcheck
"""
import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # the GPU host is headless
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent))
from analysis import (HYPOTHESES, RECALL_GUARD, finalise, latest_runs,  # noqa: E402
                      load_jsonl, report, wilson_ci)

INK = "#1f1f1f"
MUTED = "#8a8a8a"
SERIES = (("recall", "#2f6f4e", "Recall (MAL)"),
          ("fpr_hn", "#9d2b35", "FPR hard negative"),
          ("fpr_typ", "#b07d2b", "FPR typical"))


# dominates reports whether a beats b on every objective and strictly wins on one.
def dominates(a, b, senses):
    better = False
    for left, right, sense in zip(a, b, senses):
        if sense * left < sense * right:
            return False
        if sense * left > sense * right:
            better = True
    return better


# pareto_front returns the indices of the points no other point dominates.
def pareto_front(points, senses):
    return [i for i, point in enumerate(points)
            if not any(dominates(other, point, senses)
                       for j, other in enumerate(points) if j != i)]


# bounds returns a rate's Wilson interval as distances below and above it.
def bounds(rate, n):
    if not n or rate is None:
        return 0.0, 0.0
    low, high = wilson_ci(round(rate * n), n)
    return rate - low, high - rate


def _style(ax, title, ylabel):
    ax.set_title(title, fontsize=10, color=INK, loc="left")
    ax.set_ylabel(ylabel, fontsize=9, color=INK)
    ax.tick_params(labelsize=8, colors=INK)
    ax.grid(axis="y", color="#e2e2e2", lw=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)


# plot_rates draws recall and both false positive rates per configuration.
def plot_rates(reports, path):
    fig, axes = plt.subplots(len(reports), 1, figsize=(9, 3.4 * len(reports)), squeeze=False)
    for ax, entry in zip(axes[:, 0], reports):
        configs = sorted(entry["descriptive"])
        width = 0.26
        for offset, (key, colour, label) in zip((-width, 0.0, width), SERIES):
            values, lows, highs = [], [], []
            for config in configs:
                cell = entry["descriptive"][config]
                value = cell[key] or 0.0
                low, high = bounds(cell[key], cell[f"{key}_n"])
                values.append(value)
                lows.append(low)
                highs.append(high)
            x = [i + offset for i in range(len(configs))]
            ax.bar(x, values, width, color=colour, label=label)
            # The interval is what tells a real gap from four pairs of noise.
            ax.errorbar(x, values, yerr=[lows, highs], fmt="none", ecolor=INK, capsize=3, lw=0.9)
        ax.set_xticks(range(len(configs)))
        ax.set_xticklabels(configs, fontsize=8)
        ax.set_ylim(0, 1.05)
        _style(ax, entry["model"], "rate")
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, fontsize=8, frameon=False, ncol=3, loc="lower center")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(path, dpi=160)
    plt.close(fig)


# plot_tests draws each confirmatory comparison beside its recall guard.
def plot_tests(reports, path):
    tests = [test for entry in reports for test in entry["tests"]]
    fig, (left, right) = plt.subplots(1, 2, figsize=(11, 0.6 * len(tests) + 2.4))
    rows = range(len(tests))

    for y, test in zip(rows, tests):
        base, var = test["fpr_baseline"] or 0.0, test["fpr_variant"] or 0.0
        expected = HYPOTHESES[test["hypothesis"]]["direction"] == "up"
        moved_right = (var > base) if expected else (var < base)
        left.plot([base, var], [y, y], color=MUTED, lw=1.2, zorder=1)
        left.scatter([base], [y], s=34, color=MUTED, zorder=2)
        left.scatter([var], [y], s=46, zorder=3,
                     color="#2f6f4e" if moved_right else "#9d2b35")
        left.text(1.02, y, f"p={test['p_holm']:.3f}", fontsize=7, va="center", color=INK)

        delta, (low, high) = test["recall_delta_pt"], test["recall_ci_pt"]
        right.plot([low, high], [y, y], color=MUTED, lw=1.2)
        right.scatter([delta], [y], s=40, color=INK, zorder=3)

    labels = [f"{t['model'].split('/')[-1][:22]}  {t['hypothesis']}: "
              f"{t['baseline']}→{t['variant']}" for t in tests]
    for ax in (left, right):
        ax.set_yticks(list(rows))
        ax.set_yticklabels(labels, fontsize=7)
        ax.invert_yaxis()
    left.set_xlim(-0.05, 1.25)
    _style(left, "FPR hard negative: baseline → variant", "")
    right.axvline(0, color=MUTED, lw=0.8)
    right.axvline(RECALL_GUARD, color="#9d2b35", lw=1.0, ls="--")
    # The guard is the whole point of the panel, so keep it on screen even when
    # every interval sits far to its right.
    span = [RECALL_GUARD] + [v for t in tests for v in (*t["recall_ci_pt"], t["recall_delta_pt"])]
    right.set_xlim(min(span) - 4, max(span) + 4)
    _style(right, f"Recall change (pt), guard at {RECALL_GUARD:g}", "")
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


# plot_pareto draws the cost trade-off and rings the non-dominated configurations.
def plot_pareto(reports, path):
    fig, axes = plt.subplots(1, len(reports), figsize=(5.4 * len(reports), 4.4), squeeze=False)
    for ax, entry in zip(axes[0], reports):
        configs = sorted(entry["descriptive"])
        cells = [entry["descriptive"][c] for c in configs]
        points = [(c["fpr_hn"] or 0.0, c["recall"] or 0.0, c["median_latency_ms"] or 0.0)
                  for c in cells]
        # Lower false positives, higher recall, lower latency.
        front = set(pareto_front(points, (-1, 1, -1)))
        latencies = [p[2] for p in points]
        drawn = ax.scatter([p[0] for p in points], [p[1] for p in points],
                           c=latencies, cmap="cividis", s=110, edgecolor=INK, lw=0.6, zorder=2)
        ax.scatter([points[i][0] for i in front], [points[i][1] for i in front],
                   s=260, facecolors="none", edgecolor="#2f6f4e", lw=1.6, zorder=1)
        # Configurations that tie land on one marker, so they share one label
        # rather than stacking unreadably on top of each other.
        shared = {}
        for config, (x, y, _) in zip(configs, points):
            shared.setdefault((x, y), []).append(config)
        for (x, y), names in shared.items():
            ax.annotate(", ".join(names), (x, y), fontsize=7, xytext=(5, 5),
                        textcoords="offset points", color=INK)
        ax.set_xlabel("FPR hard negative", fontsize=9)
        _style(ax, entry["model"], "recall (MAL)")
        fig.colorbar(drawn, ax=ax, label="median latency (ms)")
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", default="data/results.jsonl")
    parser.add_argument("--pairs", default="data/pairs.jsonl")
    parser.add_argument("--out", default="figures")
    parser.add_argument("--invalid-as", default="benign", choices=("benign", "malicious"))
    args = parser.parse_args(argv)

    results, pairs = latest_runs(load_jsonl(args.results)), load_jsonl(args.pairs)
    models = sorted({row["model"] for row in results if row.get("model")})
    reports = finalise([report(results, pairs, m, args.invalid_as) for m in models],
                       results, pairs)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for name, draw in (("detection_rates", plot_rates), ("hypothesis_tests", plot_tests),
                       ("cost_pareto", plot_pareto)):
        target = out / f"{name}.png"
        draw(reports, target)
        print(target)


def selfcheck():
    senses = (-1, 1)  # minimise the first, maximise the second

    # A point beaten on both axes is dominated; a trade-off keeps both.
    assert dominates((0.1, 0.9), (0.2, 0.8), senses)
    assert not dominates((0.1, 0.9), (0.1, 0.9), senses), "a tie dominates nothing"
    assert pareto_front([(0.1, 0.9), (0.2, 0.8)], senses) == [0]
    assert pareto_front([(0.1, 0.5), (0.3, 0.9)], senses) == [0, 1]
    # Duplicates are non-dominated, so neither may be dropped silently.
    assert pareto_front([(0.1, 0.9), (0.1, 0.9)], senses) == [0, 1]

    assert bounds(None, 0) == (0.0, 0.0) and bounds(0.5, 0) == (0.0, 0.0)
    low, high = bounds(0.5, 4)
    assert low > 0 and high > 0, "four pairs must not read as a certainty"
    assert bounds(0.5, 400)[0] < low, "a wider sample narrows the interval"

    print("ok")


if __name__ == "__main__":
    if "--selfcheck" in sys.argv:
        selfcheck()
    else:
        main()
