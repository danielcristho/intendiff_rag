"""Result tables as a workbook, for drafting the manuscript.

    python pipeline/tables.py --results data/results.jsonl --pairs data/pairs.jsonl
    python pipeline/tables.py --selfcheck
"""
import argparse
import math
import sys
from pathlib import Path

from openpyxl import Workbook
from openpyxl.drawing.image import Image as SheetImage
from openpyxl.styles import Alignment, Font
from openpyxl.utils import get_column_letter

sys.path.insert(0, str(Path(__file__).parent))
from analysis import (finalise, latest_runs, load_jsonl, report,  # noqa: E402
                      wilson_ci)

RATE_COLUMNS = (("recall", "Recall (MAL)"), ("fpr_hn", "FPR hard negative"),
                ("fpr_typ", "FPR typical"))
FIGURES = (
    ("fig_rates",
     "Detection rates per configuration, with 95% Wilson intervals. (a) recall on "
     "malicious updates, (b) false positive rate on hard negatives, (c) false "
     "positive rate on typical updates."),
    ("fig_hypotheses",
     "Confirmatory comparisons, one column per model. Top: false positive rate on "
     "hard negatives for baseline and variant. Bottom: recall change with its "
     "bootstrap 95% interval; the dashed line is the guard."),
    ("fig_pareto",
     "Cost against false positives. Filled markers are the configurations no other "
     "configuration beats on latency, false positive rate and recall together."),
)
FIGURE_WIDTH_PX = 900
ROW_HEIGHT_PX = 20  # Excel's default row, in the units add_image() measures in


# interval formats a rate and its Wilson bounds the way a results table reads.
def interval(rate, n):
    if not n or rate is None:
        return ""
    low, high = wilson_ci(round(rate * n), n)
    return f"{rate * 100:.1f} [{low * 100:.1f}, {high * 100:.1f}]"


def _write(sheet, header, rows):
    sheet.append(header)
    for cell in sheet[1]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    for row in rows:
        sheet.append(row)
    sheet.freeze_panes = "A2"
    for index, title in enumerate(header, start=1):
        width = max([len(str(title))] + [len(str(row[index - 1])) for row in rows])
        sheet.column_dimensions[get_column_letter(index)].width = min(width + 3, 42)


# rate_rows lists every configuration's rates, costs and sample sizes.
def rate_rows(reports):
    rows = []
    for entry in reports:
        for config, cell in sorted(entry["descriptive"].items()):
            rows.append([
                entry["model"], config,
                *[interval(cell[key], cell[f"{key}_n"]) for key, _ in RATE_COLUMNS],
                cell["recall_n"], cell["fpr_hn_n"], cell["fpr_typ_n"],
                round(cell["json_validity"], 3),
                cell["median_latency_ms"], cell["p95_latency_ms"],
                round(cell["mean_prompt_tokens"], 1), round(cell["mean_completion_tokens"], 1),
            ])
    return rows


# test_rows lists each confirmatory comparison with its corrected p value.
def test_rows(reports):
    rows = []
    for entry in reports:
        for test in entry["tests"]:
            only_baseline, only_variant = test["discordant"]
            low, high = test["recall_ci_pt"]
            rows.append([
                test["model"], test["hypothesis"],
                test["baseline"], test["variant"],
                round((test["fpr_baseline"] or 0.0) * 100, 1),
                round((test["fpr_variant"] or 0.0) * 100, 1),
                only_baseline, only_variant,
                round(test["p_raw"], 4), round(test["p_holm"], 4),
                round(test["recall_delta_pt"], 1), f"[{low:.1f}, {high:.1f}]",
                test["label"],
            ])
    return rows


# reserve returns how many rows a figure block occupies, embedding the rendered
# PNG when one is already on disk.
def reserve(sheet, source, row):
    if source.exists():
        image = SheetImage(source)
        image.height = int(image.height * FIGURE_WIDTH_PX / image.width)
        image.width = FIGURE_WIDTH_PX
        sheet.add_image(image, f"A{row}")
        rows = math.ceil(image.height / ROW_HEIGHT_PX)
    else:
        rows = 18
        sheet.cell(row, 1, "(paste the figure here)").alignment = Alignment(
            horizontal="center", vertical="center")
    # An image floats above the grid instead of resizing it, so the rows under it
    # are held open by hand or the next caption lands on top of the picture.
    for offset in range(rows):
        sheet.row_dimensions[row + offset].height = ROW_HEIGHT_PX * 0.75
    return rows


# figure_sheet lays out one captioned block per figure, in manuscript order.
def figure_sheet(sheet, directory):
    sheet.column_dimensions["A"].width = 120
    row = 1
    for number, (stem, caption) in enumerate(FIGURES, start=1):
        title = sheet.cell(row, 1, f"Figure {number}. {caption}")
        title.font = Font(bold=True)
        title.alignment = Alignment(wrap_text=True, vertical="top")
        sheet.row_dimensions[row].height = 32
        sheet.cell(row + 1, 1, f"Replace with: {directory / stem}.pdf").font = Font(
            italic=True, color="808080")
        row += 3 + reserve(sheet, directory / f"{stem}.png", row + 2)
    return sheet


def build(reports, path, figures=None):
    book = Workbook()
    rates = book.worksheets[0]  # the sheet Workbook() starts with
    rates.title = "rates"
    _write(rates, ["Model", "Configuration",
                   *[f"{title} % [95% CI]" for _, title in RATE_COLUMNS],
                   "n MAL", "n HN", "n TYP", "JSON validity",
                   "Median latency (ms)", "p95 latency (ms)",
                   "Mean prompt tokens", "Mean completion tokens"],
           rate_rows(reports))
    _write(book.create_sheet("hypotheses"),
           ["Model", "Hypothesis", "Baseline", "Variant",
            "FPR baseline %", "FPR variant %",
            "Discordant: baseline only", "Discordant: variant only",
            "p (McNemar)", "p (Holm)", "Recall change (pt)", "Recall 95% CI (pt)",
            "Verdict"],
           test_rows(reports))
    figure_sheet(book.create_sheet("figures"), figures or Path(path).parent)
    book.save(path)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", default="data/results.jsonl")
    parser.add_argument("--pairs", default="data/pairs.jsonl")
    parser.add_argument("--out", default="data/figures/results.xlsx")
    parser.add_argument("--invalid-as", default="benign", choices=("benign", "malicious"))
    args = parser.parse_args(argv)

    results, pairs = latest_runs(load_jsonl(args.results)), load_jsonl(args.pairs)
    models = sorted({row["model"] for row in results if row.get("model")})
    reports = finalise([report(results, pairs, model, args.invalid_as) for model in models],
                       results, pairs)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    build(reports, out)
    print(out)


def selfcheck():
    assert interval(None, 0) == "" and interval(0.5, 0) == ""
    # A rate of 1.0 must not print an interval that reaches past 100%.
    text = interval(1.0, 4)
    assert text.startswith("100.0 [") and text.endswith("100.0]"), text
    assert interval(0.0, 2).startswith("0.0 [0.0,"), interval(0.0, 2)

    sample = [{
        "model": "m", "descriptive": {"E0": {
            "recall": 1.0, "recall_n": 1, "fpr_hn": 0.0, "fpr_hn_n": 2,
            "fpr_typ": 0.0, "fpr_typ_n": 1, "json_validity": 1.0,
            "median_latency_ms": 700.0, "p95_latency_ms": 900.0,
            "mean_prompt_tokens": 400.0, "mean_completion_tokens": 100.0}},
        "tests": [{"model": "m", "hypothesis": "H3", "baseline": "E4-noint",
                   "variant": "E4", "fpr_baseline": 0.5, "fpr_variant": 0.0,
                   "discordant": [1, 0], "p_raw": 1.0, "p_holm": 1.0,
                   "recall_delta_pt": 0.0, "recall_ci_pt": [-1.0, 1.0],
                   "label": "inconclusive"}]}]
    assert len(rate_rows(sample)[0]) == 13, rate_rows(sample)[0]
    assert len(test_rows(sample)[0]) == 13, test_rows(sample)[0]

    import tempfile
    from openpyxl import load_workbook
    scratch = Path(tempfile.mkdtemp())
    target = scratch / "t.xlsx"
    build(sample, target)
    book = load_workbook(target)
    assert book.sheetnames == ["rates", "hypotheses", "figures"], book.sheetnames

    # With no rendered PNG to hand, every figure still gets its own block.
    sheet = book["figures"]
    captions = [c.value for c in sheet["A"] if c.value and str(c.value).startswith("Figure ")]
    assert len(captions) == len(FIGURES), captions
    rows = [c.row for c in sheet["A"] if c.value and str(c.value).startswith("Figure ")]
    assert rows == sorted(set(rows)) and rows[1] - rows[0] > 18, rows

    print("ok")


if __name__ == "__main__":
    if "--selfcheck" in sys.argv:
        selfcheck()
    else:
        main()
