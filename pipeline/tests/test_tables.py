from openpyxl import load_workbook

from pipeline.results.tables import FIGURES, build, interval, rate_rows, test_rows
from pipeline.tests.fixtures import temp_dir

SAMPLE = [{"model": "m", "descriptive": {"E0": {
    "recall": 1.0, "recall_n": 1, "fpr_hn": 0.0, "fpr_hn_n": 2, "fpr_typ": 0.0, "fpr_typ_n": 1,
    "json_validity": 1.0, "median_latency_ms": 700.0, "p95_latency_ms": 900.0,
    "mean_prompt_tokens": 400.0, "mean_completion_tokens": 100.0}},
    "tests": [{"model": "m", "comparison": "C1", "baseline": "E4-noint", "variant": "E4",
               "fpr_baseline": 0.5, "fpr_variant": 0.0, "discordant": [1, 0], "p_raw": 1.0, "p_holm": 1.0,
               "recall_delta_pt": 0.0, "recall_ci_pt": [-1.0, 1.0], "label": "inconclusive"}]}]


def test_an_interval_never_passes_one_hundred_percent():
    assert interval(None, 0) == "" and interval(0.5, 0) == ""
    text = interval(1.0, 4)
    assert text.startswith("100.0 [") and text.endswith("100.0]")


def test_the_workbook_has_its_sheets_and_one_block_per_figure():
    assert len(rate_rows(SAMPLE)[0]) == 13 and len(test_rows(SAMPLE)[0]) == 13
    target = temp_dir() / "t.xlsx"
    build(SAMPLE, target)
    book = load_workbook(target)
    assert book.sheetnames == ["rates", "comparisons", "figures"]
    rows = [c.row for c in book["figures"]["A"] if c.value and str(c.value).startswith("Figure ")]
    assert len(rows) == len(FIGURES) and rows[1] - rows[0] > 18
