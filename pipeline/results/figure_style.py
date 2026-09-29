"""Shared look of the result figures, and the helpers their labels need."""
import matplotlib

matplotlib.use("Agg")  # the GPU host is headless
import matplotlib.pyplot as plt  # noqa: E402

from pipeline.results.statistics import wilson_ci  # noqa: E402

# STYLE sizes figures for a manuscript column: 8 pt sans, horizontal rules, legend above the axes.
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
# WHISKER darkens each colour, since a 0% bar has no body and its interval names the model.
WHISKER = {GREY: "0.3", BLUE: "#18496f"}
PANELS = (("recall", "Recall on MAL"), ("fpr_hn", "FPR on hard negatives"),
          ("fpr_typ", "FPR on typical"))


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


# configs_of collects every configuration seen, so a model missing one keeps its alignment.
def configs_of(reports):
    return sorted({config for entry in reports for config in entry["descriptive"]})


def legend(fig, handles):
    fig.legend(handles=handles, loc="upper center", ncol=len(handles),
               frameon=False, bbox_to_anchor=(0.5, 1.0))


# save writes the vector copy for LaTeX beside a raster copy to glance at.
def save(fig, stem):
    for suffix in (".pdf", ".png"):
        fig.savefig(stem.with_suffix(suffix), bbox_inches="tight")
    plt.close(fig)
