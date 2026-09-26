"""Figures for the result tables.

    python pipeline/plots.py --results data/results.jsonl --pairs data/pairs.jsonl --out data/figures
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

# Sized for a manuscript column: 8 pt sans, horizontal rules only, and a legend
# above the axes rather than inside them.
STYLE = {
    "font.family": "sans-serif", "font.sans-serif": ["DejaVu Sans"],
    "font.size": 8, "axes.titlesize": 8, "axes.labelsize": 8,
    "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 7,
    "axes.linewidth": 0.6, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "axes.grid.axis": "y", "axes.axisbelow": True,
    "grid.color": "0.88", "grid.linewidth": 0.6, "savefig.dpi": 300,
    "pdf.fonttype": 42,  # embed real glyphs; some venues reject type 3
}
GREY, BLUE, GREEN = "#7f7f7f", "#2878b5", "#2ca089"
# Darker twins for the whiskers: a 0% bar has no body, so its interval is
# the only thing left to say which model it belongs to.
WHISKER = {GREY: "0.3", BLUE: "#18496f"}
PANELS = (("recall", "Recall on MAL"), ("fpr_hn", "FPR on hard negatives"),
          ("fpr_typ", "FPR on typical"))


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


# bounds returns a rate's Wilson interval in points, as distances below and above it.
def bounds(rate, n):
    if not n or rate is None:
        return 0.0, 0.0
    low, high = wilson_ci(round(rate * n), n)
    return (rate - low) * 100, (high - rate) * 100


# short_model trims a Hugging Face identifier down to what fits a tick label.
def short_model(name):
    return name.split("/")[-1].replace("-Instruct", "").replace("-2507", "")


# wrap_label breaks a configuration name at its hyphen so tick labels stay narrow.
def wrap_label(name):
    return name.replace("-", "-\n", 1)


# configs_of collects every configuration seen, so a model missing one still lines up.
def configs_of(reports):
    return sorted({config for entry in reports for config in entry["descriptive"]})


def _legend(fig, handles):
    fig.legend(handles=handles, loc="upper center", ncol=len(handles),
               frameon=False, bbox_to_anchor=(0.5, 1.0))


# save writes the vector copy for LaTeX beside a raster copy to glance at.
def save(fig, stem):
    for suffix in (".pdf", ".png"):
        fig.savefig(stem.with_suffix(suffix), bbox_inches="tight")
    plt.close(fig)


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
            # The edge keeps a 0% bar visible as a rule at the baseline; without
            # it an all-zero panel reads as missing data rather than as a result.
            ax.bar(x, values, width, color=colour, edgecolor=colour, linewidth=0.8,
                   label=short_model(entry["model"]))
            # Without the interval, four pairs at 100% look like a finding.
            ax.errorbar(x, values, yerr=[lows, highs], fmt="none",
                        ecolor=WHISKER[colour], elinewidth=0.7, capsize=1.6)
        ax.set_title(f"({chr(97 + panel)}) {title} (%)", loc="left")
        ax.set_xticks(range(len(configs)))
        ax.set_xticklabels([wrap_label(config) for config in configs])
        ax.set_ylim(0, 105)
    _legend(fig, axes[0].get_legend_handles_labels()[0])
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    save(fig, stem)


# plot_hypotheses draws where each comparison moved the false positive rate and
# what it cost in recall, one column per model.
def plot_hypotheses(reports, stem):
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
        top.set_xticklabels([test["hypothesis"] for test in tests])

        for index, test in enumerate(tests):
            delta, (low, high) = test["recall_delta_pt"], test["recall_ci_pt"]
            # H2a predicts the false positive rate rises and is not traded against
            # recall, so the guard line below does not gate it. A filled marker
            # would invite reading it as though it did.
            gated = HYPOTHESES[test["hypothesis"]]["recall_guard"]
            bottom.errorbar([index], [delta], yerr=[[delta - low], [high - delta]],
                            fmt="o", ms=3.6, color=GREEN, mfc=GREEN if gated else "white",
                            mew=0.9, ecolor="0.35", elinewidth=0.8, capsize=2)
        bottom.axhline(0, color="0.8", lw=0.6)
        bottom.axhline(RECALL_GUARD, color="0.2", lw=0.9, ls=(0, (4, 2)),
                       label=f"Recall guard ({RECALL_GUARD:g} pt)")
        bottom.plot([], [], "o", ms=3.6, color=GREEN, mfc="white", mew=0.9,
                    label="Guard not applied")
        bottom.set_xticks(range(len(tests)))
        bottom.set_xticklabels([f"{t['hypothesis']}\n{t['baseline']}→{t['variant']}"
                                for t in tests])
    axes[0][0].set_ylabel("FPR on hard negatives (%)")
    axes[1][0].set_ylabel("Recall change (pt)")
    _legend(fig, axes[0][0].get_legend_handles_labels()[0]
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
        # Cheaper, fewer false positives, higher recall. Recall stays an
        # objective even though the axes show only the first two.
        front = set(pareto_front(points, (-1, -1, 1)))
        named = {}
        for index, (config, point) in enumerate(zip(configs, points)):
            on_front = index in front
            ax.plot([point[0]], [point[1]], "o", ms=5.0 if on_front else 4.0,
                    mfc=BLUE if on_front else "white", mec=BLUE if on_front else GREY,
                    mew=0.9, zorder=2 if on_front else 1)
            if on_front:
                named.setdefault(point[:2], []).append(config)
        # Only the front is labelled; naming dominated points buries the answer.
        for (x, y), names in named.items():
            ax.annotate(", ".join(names), (x, y), fontsize=6.5, xytext=(4, 4),
                        textcoords="offset points")
        ax.set_title(f"({chr(97 + column)}) {short_model(entry['model'])}", loc="left")
        ax.set_xlabel("Median latency (ms)")
    axes[0][0].set_ylabel("FPR on hard negatives (%)")
    _legend(fig, [plt.Line2D([], [], marker="o", ls="", ms=5.0, mfc=BLUE, mec=BLUE,
                             label="Pareto-optimal"),
                  plt.Line2D([], [], marker="o", ls="", ms=4.0, mfc="white", mec=GREY,
                             mew=0.9, label="Dominated")])
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    save(fig, stem)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", default="data/results.jsonl")
    parser.add_argument("--pairs", default="data/pairs.jsonl")
    parser.add_argument("--out", default="data/figures")
    parser.add_argument("--invalid-as", default="benign", choices=("benign", "malicious"))
    args = parser.parse_args(argv)

    results, pairs = latest_runs(load_jsonl(args.results)), load_jsonl(args.pairs)
    models = sorted({row["model"] for row in results if row.get("model")})
    reports = finalise([report(results, pairs, model, args.invalid_as) for model in models],
                       results, pairs)

    plt.rcParams.update(STYLE)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for name, draw in (("fig_rates", plot_rates), ("fig_hypotheses", plot_hypotheses),
                       ("fig_pareto", plot_pareto)):
        draw(reports, out / name)
        print(out / f"{name}.pdf")


def selfcheck():
    senses = (-1, 1)  # minimise the first, maximise the second

    # A point beaten on both axes is dominated; a trade-off keeps both.
    assert dominates((0.1, 0.9), (0.2, 0.8), senses)
    assert not dominates((0.1, 0.9), (0.1, 0.9), senses), "a tie dominates nothing"
    assert pareto_front([(0.1, 0.9), (0.2, 0.8)], senses) == [0]
    assert pareto_front([(0.1, 0.5), (0.3, 0.9)], senses) == [0, 1]
    # Duplicates are non-dominated, so neither may be dropped silently.
    assert pareto_front([(0.1, 0.9), (0.1, 0.9)], senses) == [0, 1]
    # A third objective rescues a point the first two would discard.
    assert pareto_front([(0.1, 0.9, 0.0), (0.2, 0.8, 1.0)], (-1, 1, 1)) == [0, 1]

    assert bounds(None, 0) == (0.0, 0.0) and bounds(0.5, 0) == (0.0, 0.0)
    low, high = bounds(0.5, 4)
    assert low > 0 and high > 0, "four pairs must not read as a certainty"
    assert bounds(0.5, 400)[0] < low, "a wider sample narrows the interval"
    assert bounds(1.0, 4)[0] > 20, "intervals are reported in points, not rates"

    assert short_model("Qwen/Qwen3-4B-Instruct-2507") == "Qwen3-4B"
    assert wrap_label("E4-noint") == "E4-\nnoint" and wrap_label("E0") == "E0"
    assert configs_of([{"descriptive": {"E0": {}}}, {"descriptive": {"E4": {}}}]) == ["E0", "E4"]

    print("ok")


if __name__ == "__main__":
    if "--selfcheck" in sys.argv:
        selfcheck()
    else:
        main()
