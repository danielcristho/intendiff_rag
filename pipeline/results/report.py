"""Descriptive measures and paired comparisons per model, printed as JSON."""
import argparse
import json
import sys
from collections import defaultdict

from pipeline.results.comparisons import ALPHA, COMPARISONS, moved_as_expected, outcome, wording
from pipeline.results.metrics import cost_summary, json_validity, latest_runs, rate, subset_rows
from pipeline.results.statistics import discordant, holm, mcnemar_p, recall_delta_bootstrap
from pipeline.shared.config import layout
from pipeline.shared.jsonl import read_jsonl

SUBSET_MEASURES = (("MAL", "recall"), ("HN", "fpr_hn"), ("TYP", "fpr_typ"))


def report(results, pairs, model, invalid_as="benign"):
    by_config = defaultdict(list)
    for row in results:
        if row.get("model") == model:
            by_config[row["config"]].append(row)
    descriptive = {}
    for config, rows in sorted(by_config.items()):
        entry = {"json_validity": json_validity(rows), **cost_summary(rows)}
        for subset, name in SUBSET_MEASURES:
            selected = subset_rows(rows, pairs, subset)
            entry[name], entry[f"{name}_n"] = rate(selected, invalid_as), len(selected)
        descriptive[config] = entry
    tests = []
    for name, spec in COMPARISONS.items():
        baseline = subset_rows(by_config.get(spec["baseline"], []), pairs, "HN")
        variant = subset_rows(by_config.get(spec["variant"], []), pairs, "HN")
        only_baseline, only_variant = discordant(baseline, variant, invalid_as)
        tests.append({"comparison": name, "model": model, "baseline": spec["baseline"], "variant": spec["variant"],
                      "fpr_baseline": rate(baseline, invalid_as), "fpr_variant": rate(variant, invalid_as),
                      "discordant": [only_baseline, only_variant], "p_raw": mcnemar_p(only_baseline, only_variant)})
    return {"model": model, "descriptive": descriptive, "tests": tests}


# finalise applies Holm across every test of every model at once, then scores recall and the outcome.
def finalise(reports, results, pairs):
    tests = [test for entry in reports for test in entry["tests"]]
    for test, adjusted in zip(tests, holm([test["p_raw"] for test in tests], ALPHA)):
        spec = COMPARISONS[test["comparison"]]
        model_rows = [row for row in results if row.get("model") == test["model"]]
        variant = subset_rows([r for r in model_rows if r["config"] == spec["variant"]], pairs, "MAL")
        baseline = subset_rows([r for r in model_rows if r["config"] == spec["baseline"]], pairs, "MAL")
        delta, (low, high) = recall_delta_bootstrap(variant, baseline, pairs)
        key = outcome(moved_as_expected(spec, test["fpr_baseline"], test["fpr_variant"]),
                      adjusted, delta, low, spec["recall_guard"])
        test.update({"p_holm": adjusted, "recall_delta_pt": delta, "recall_ci_pt": [low, high],
                     "outcome": key, "label": wording(key)})
    return reports


# load_reports reads the results and pairs and builds the finalised report of every model.
def load_reports(results_path, pairs_path, invalid_as="benign"):
    results, pairs = latest_runs(read_jsonl(results_path)), read_jsonl(pairs_path)
    models = sorted({row["model"] for row in results if row.get("model")})
    return finalise([report(results, pairs, model, invalid_as) for model in models], results, pairs)


def add_source_arguments(parser, data):
    parser.add_argument("--results", default=str(data.results))
    parser.add_argument("--pairs", default=str(data.pairs))
    parser.add_argument("--invalid-as", default="benign", choices=("benign", "malicious"),
                        help="how an invalid reply counts; malicious gives the sensitivity analysis")


def main(argv=None):
    data = layout()
    parser = argparse.ArgumentParser(prog="report")
    add_source_arguments(parser, data)
    args = parser.parse_args(argv)
    reports = load_reports(args.results, args.pairs, args.invalid_as)
    if not reports:
        sys.exit(f"no results in {args.results}")
    print(json.dumps({"invalid_counted_as": args.invalid_as, "models": reports},
                     ensure_ascii=False, indent=2, default=float))
