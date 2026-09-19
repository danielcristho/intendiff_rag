"""Metrics and statistics over results.jsonl.

    python pipeline/analysis.py --results data/results.jsonl --pairs data/pairs.jsonl
    python pipeline/analysis.py --selfcheck
"""
import argparse
import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

BOOTSTRAP_SEED = 2026
BOOTSTRAP_RESAMPLES = 10_000
ALPHA = 0.05
RECALL_GUARD = -5.0
WHITESPACE = re.compile(r"\s+")

HYPOTHESES = {
    "H2a": {"baseline": "E0", "variant": "E3", "direction": "up", "recall_guard": False},
    "H2b": {"baseline": "E3-k2", "variant": "E4", "direction": "down", "recall_guard": True},
    "H3": {"baseline": "E4-noint", "variant": "E4", "direction": "down", "recall_guard": True},
}


def load_jsonl(path):
    text = Path(path)
    if not text.exists():
        return []
    return [json.loads(line) for line in text.read_text().splitlines() if line.strip()]


def verdict_of(row, invalid_as="benign"):
    """Invalid output counts as benign by default, malicious under --sensitivity."""
    if not row.get("json_valid") or row.get("verdict") not in ("malicious", "benign"):
        return invalid_as
    return row["verdict"]


def called_malicious(rows, invalid_as="benign"):
    return sum(1 for row in rows if verdict_of(row, invalid_as) == "malicious")


def subset_rows(rows, pairs, subset):
    members = {pair["id"] for pair in pairs if pair.get("subset") == subset}
    return [row for row in rows if row["pair_id"] in members]


def rate(rows, invalid_as="benign"):
    """Recall and FPR are the same proportion over different subsets."""
    return (called_malicious(rows, invalid_as) / len(rows)) if rows else 0.0


def json_validity(rows):
    return (sum(1 for row in rows if row.get("json_valid")) / len(rows)) if rows else 0.0


def normalise(text):
    return WHITESPACE.sub(" ", str(text)).strip()


def evidence_hits_gold(row, gold_lines):
    """A match is a substring either way, once whitespace is normalised."""
    for item in row.get("evidence") or ():
        candidate = normalise(item)
        if not candidate:
            continue
        for gold in gold_lines:
            reference = normalise(gold)
            if reference and (candidate in reference or reference in candidate):
                return True
    return False


def evidence_localization(rows, pairs, invalid_as="benign"):
    """Over true positives only."""
    gold = {pair["id"]: pair.get("gold_evidence") or [] for pair in pairs}
    positives = [row for row in rows if verdict_of(row, invalid_as) == "malicious"]
    if not positives:
        return 0.0
    return sum(1 for row in positives if evidence_hits_gold(row, gold.get(row["pair_id"], []))) / len(positives)


def flip_rate(rows, invalid_as="benign"):
    """Share of pairs whose verdict is not the same across every seed."""
    by_pair = defaultdict(set)
    for row in rows:
        by_pair[row["pair_id"]].add(verdict_of(row, invalid_as))
    return (sum(1 for seen in by_pair.values() if len(seen) > 1) / len(by_pair)) if by_pair else 0.0


def percentile_nearest_rank(values, fraction):
    """Nearest-rank; numpy.percentile interpolates and would not match."""
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(1, math.ceil(fraction * len(ordered)))
    return ordered[min(index, len(ordered)) - 1]


def cost_summary(rows):
    latencies = [row["latency_ms"] for row in rows if row.get("latency_ms") is not None]
    prompt = [row["prompt_tokens"] for row in rows if row.get("prompt_tokens") is not None]
    completion = [row["completion_tokens"] for row in rows if row.get("completion_tokens") is not None]
    return {
        "median_latency_ms": percentile_nearest_rank(latencies, 0.5),
        "p95_latency_ms": percentile_nearest_rank(latencies, 0.95),
        "mean_prompt_tokens": (sum(prompt) / len(prompt)) if prompt else 0.0,
        "mean_completion_tokens": (sum(completion) / len(completion)) if completion else 0.0,
    }


def discordant(baseline_rows, variant_rows, invalid_as="benign"):
    """The (b, c) cells McNemar needs."""
    baseline = {row["pair_id"]: verdict_of(row, invalid_as) for row in baseline_rows}
    variant = {row["pair_id"]: verdict_of(row, invalid_as) for row in variant_rows}
    only_baseline = only_variant = 0
    for pair_id, before in baseline.items():
        after = variant.get(pair_id)
        if after is None or after == before:
            continue
        if before == "malicious":
            only_baseline += 1
        else:
            only_variant += 1
    return only_baseline, only_variant


def recall_delta_bootstrap(variant_rows, baseline_rows, pairs,
                           resamples=BOOTSTRAP_RESAMPLES, seed=BOOTSTRAP_SEED):
    """Resamples campaigns, not pairs: pairs within one are correlated."""
    campaign_of = {pair["id"]: pair.get("campaign") or pair["id"] for pair in pairs}
    members = defaultdict(list)
    for pair_id, campaign in campaign_of.items():
        members[campaign].append(pair_id)

    variant = {row["pair_id"]: verdict_of(row) for row in variant_rows}
    baseline = {row["pair_id"]: verdict_of(row) for row in baseline_rows}
    campaigns = sorted(members)
    if not campaigns:
        return 0.0, (0.0, 0.0)

    def recall_over(pair_ids, table):
        scored = [table[pid] for pid in pair_ids if pid in table]
        return (sum(1 for v in scored if v == "malicious") / len(scored)) if scored else 0.0

    every_pair = [pid for campaign in campaigns for pid in members[campaign]]
    observed = recall_over(every_pair, variant) - recall_over(every_pair, baseline)

    rng = np.random.default_rng(seed)
    deltas = []
    for _ in range(resamples):
        drawn = rng.choice(len(campaigns), size=len(campaigns), replace=True)
        sampled = [pid for index in drawn for pid in members[campaigns[index]]]
        deltas.append(recall_over(sampled, variant) - recall_over(sampled, baseline))

    low, high = np.percentile(deltas, [2.5, 97.5])
    return observed * 100, (low * 100, high * 100)


def label_hypothesis(moved_right_way, p_holm, recall_delta, recall_low, guard_on_recall=True):
    """Four outcomes; H2a passes guard_on_recall=False."""
    if not moved_right_way:
        return "Tidak didukung"
    if guard_on_recall and recall_delta < RECALL_GUARD:
        return "Tidak didukung"
    if p_holm >= ALPHA:
        return "Arah sesuai, tidak signifikan"
    if not guard_on_recall:
        return "Didukung"
    return "Didukung" if recall_low >= RECALL_GUARD else "Didukung sebagian"


# --- statsmodels seam (D43) ---------------------------------------------------

def _statsmodels(module):
    try:
        return __import__(module, fromlist=["*"])
    except ImportError as exc:  # pragma: no cover - depends on the host
        raise RuntimeError(f"statsmodels is the locked implementation; {module} is unavailable") from exc


def wilson_ci(successes, total):
    if total == 0:
        return (0.0, 0.0)
    proportion = _statsmodels("statsmodels.stats.proportion")
    return proportion.proportion_confint(successes, total, alpha=ALPHA, method="wilson")


def mcnemar_p(only_baseline, only_variant):
    if only_baseline + only_variant == 0:
        return 1.0  # No discordant pairs, nothing to test.
    tables = _statsmodels("statsmodels.stats.contingency_tables")
    return float(tables.mcnemar([[0, only_baseline], [only_variant, 0]], exact=True).pvalue)


def holm(pvalues):
    if not pvalues:
        return []
    multitest = _statsmodels("statsmodels.stats.multitest")
    return list(multitest.multipletests(pvalues, alpha=ALPHA, method="holm")[1])


def cohens_kappa(table):
    inter_rater = _statsmodels("statsmodels.stats.inter_rater")
    return float(inter_rater.cohens_kappa(np.asarray(table)).kappa)


# --- report -------------------------------------------------------------------

def report(results, pairs, model, invalid_as="benign"):
    rows = [row for row in results if row.get("model") == model]
    by_config = defaultdict(list)
    for row in rows:
        by_config[row["config"]].append(row)

    descriptive = {}
    for config, config_rows in sorted(by_config.items()):
        entry = {"json_validity": json_validity(config_rows), **cost_summary(config_rows)}
        for subset, name in (("MAL", "recall"), ("HN", "fpr_hn"), ("TYP", "fpr_typ")):
            selected = subset_rows(config_rows, pairs, subset)
            entry[name] = rate(selected, invalid_as)
            entry[f"{name}_n"] = len(selected)
        descriptive[config] = entry

    tests = []
    for name, spec in HYPOTHESES.items():
        baseline = subset_rows(by_config.get(spec["baseline"], []), pairs, "HN")
        variant = subset_rows(by_config.get(spec["variant"], []), pairs, "HN")
        only_baseline, only_variant = discordant(baseline, variant, invalid_as)
        tests.append({
            "hypothesis": name, "model": model,
            "baseline": spec["baseline"], "variant": spec["variant"],
            "fpr_baseline": rate(baseline, invalid_as), "fpr_variant": rate(variant, invalid_as),
            "discordant": [only_baseline, only_variant],
            "p_raw": mcnemar_p(only_baseline, only_variant),
        })
    return {"model": model, "descriptive": descriptive, "tests": tests}


def finalise(reports, results, pairs):
    """Holm corrects across every test at once, so it cannot live in report()."""
    tests = [test for entry in reports for test in entry["tests"]]
    for test, adjusted in zip(tests, holm([test["p_raw"] for test in tests])):
        test["p_holm"] = adjusted
        spec = HYPOTHESES[test["hypothesis"]]

        moved = (test["fpr_variant"] > test["fpr_baseline"]) if spec["direction"] == "up" \
            else (test["fpr_variant"] < test["fpr_baseline"])

        model_rows = [row for row in results if row.get("model") == test["model"]]
        variant = subset_rows([r for r in model_rows if r["config"] == spec["variant"]], pairs, "MAL")
        baseline = subset_rows([r for r in model_rows if r["config"] == spec["baseline"]], pairs, "MAL")
        delta, (low, high) = recall_delta_bootstrap(variant, baseline, pairs)

        test.update({
            "recall_delta_pt": delta, "recall_ci_pt": [low, high],
            "label": label_hypothesis(moved, adjusted, delta, low, spec["recall_guard"]),
        })
    return reports


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", default="data/results.jsonl")
    parser.add_argument("--pairs", default="data/pairs.jsonl")
    parser.add_argument("--sensitivity", action="store_true",
                        help="D18 sensitivity analysis: count invalid output as malicious")
    args = parser.parse_args(argv)

    results, pairs = load_jsonl(args.results), load_jsonl(args.pairs)
    if not results:
        sys.exit(f"no results in {args.results}")

    invalid_as = "malicious" if args.sensitivity else "benign"
    models = sorted({row.get("model") for row in results if row.get("model")})
    reports = finalise([report(results, pairs, model, invalid_as) for model in models], results, pairs)
    print(json.dumps({"invalid_counted_as": invalid_as, "models": reports},
                     ensure_ascii=False, indent=2, default=float))


def selfcheck():
    row = lambda pid, cfg, verdict, **kw: {  # noqa: E731
        "pair_id": pid, "config": cfg, "model": "m", "verdict": verdict,
        "json_valid": kw.pop("json_valid", True), **kw
    }

    # D18: an unparsable answer is benign in the main analysis, malicious in the
    # sensitivity one.
    broken = row("p1", "E0", None, json_valid=False)
    assert verdict_of(broken) == "benign"
    assert verdict_of(broken, "malicious") == "malicious"
    # A parsed row with a nonsense verdict is invalid too.
    assert verdict_of(row("p1", "E0", "suspicious")) == "benign"

    pairs = [
        {"id": "m1", "subset": "MAL", "campaign": "c1", "gold_evidence": ["+  eval(payload);"]},
        {"id": "m2", "subset": "MAL", "campaign": "c1"},
        {"id": "h1", "subset": "HN", "campaign": "c2"},
        {"id": "h2", "subset": "HN", "campaign": "c3"},
        {"id": "t1", "subset": "TYP", "campaign": "c4"},
    ]
    rows = [row("m1", "E0", "malicious"), row("m2", "E0", "benign"),
            row("h1", "E0", "malicious"), row("h2", "E0", "benign"),
            row("t1", "E0", "benign")]

    assert rate(subset_rows(rows, pairs, "MAL")) == 0.5
    assert rate(subset_rows(rows, pairs, "HN")) == 0.5
    assert rate(subset_rows(rows, pairs, "TYP")) == 0.0
    assert rate([]) == 0.0, "an empty subset must not divide by zero"

    assert json_validity(rows) == 1.0
    assert json_validity([broken]) == 0.0

    # Evidence matches in either direction once whitespace is normalised (§11.1).
    hit = row("m1", "E0", "malicious", evidence=["+   eval(payload);"])
    miss = row("m1", "E0", "malicious", evidence=["+  require('fs');"])
    assert evidence_localization([hit], pairs) == 1.0
    assert evidence_localization([miss], pairs) == 0.0
    # A pair with no gold lines cannot count as located.
    assert evidence_localization([row("m2", "E0", "malicious", evidence=["x"])], pairs) == 0.0

    # EA2 counts pairs that disagree across seeds, not individual runs.
    steady = [row("p1", "E0", "benign"), row("p1", "E0", "benign")]
    wobbly = [row("p1", "E0", "benign"), row("p1", "E0", "malicious")]
    assert flip_rate(steady) == 0.0 and flip_rate(wobbly) == 1.0

    # Nearest-rank, so p95 of ten values is the tenth, never an interpolation.
    assert percentile_nearest_rank(list(range(1, 11)), 0.95) == 10
    assert percentile_nearest_rank(list(range(1, 11)), 0.5) == 5
    assert percentile_nearest_rank([], 0.5) == 0.0

    # McNemar's b and c: only the pairs the two configurations disagree on.
    baseline = [row("h1", "E0", "malicious"), row("h2", "E0", "malicious")]
    variant = [row("h1", "E4", "benign"), row("h2", "E4", "malicious")]
    assert discordant(baseline, variant) == (1, 0)
    assert discordant(variant, baseline) == (0, 1)
    assert discordant(baseline, baseline) == (0, 0)
    assert mcnemar_p(0, 0) == 1.0, "no discordant pairs means p = 1 (§11.2)"

    # The bootstrap draws campaigns, so two pairs sharing one campaign can never
    # land in a resample separately.
    mal = [p for p in pairs if p["subset"] == "MAL"]
    better = [row("m1", "E4", "malicious"), row("m2", "E4", "malicious")]
    worse = [row("m1", "E0", "malicious"), row("m2", "E0", "benign")]
    delta, (low, high) = recall_delta_bootstrap(better, worse, mal, resamples=200)
    assert abs(delta - 50.0) < 1e-6, delta
    assert low <= delta <= high, (low, delta, high)
    # Identical inputs leave no room for the interval to move.
    flat, (flat_low, flat_high) = recall_delta_bootstrap(worse, worse, mal, resamples=200)
    assert flat == 0.0 and flat_low == flat_high == 0.0

    # Same seed, same interval: D43 requires the analysis to reproduce exactly.
    again, _ = recall_delta_bootstrap(better, worse, mal, resamples=200)
    assert again == delta

    # All four outcomes.
    assert label_hypothesis(True, 0.01, -1.0, -3.0) == "Didukung"
    assert label_hypothesis(True, 0.01, -1.0, -9.0) == "Didukung sebagian"
    assert label_hypothesis(True, 0.30, -1.0, -3.0) == "Arah sesuai, tidak signifikan"
    assert label_hypothesis(False, 0.01, -1.0, -3.0) == "Tidak didukung"
    # A recall drop past the guard fails regardless of significance.
    assert label_hypothesis(True, 0.001, -7.0, -9.0) == "Tidak didukung"
    # H2a carries no recall condition.
    assert label_hypothesis(True, 0.01, -40.0, -60.0, guard_on_recall=False) == "Didukung"

    print("ok")


if __name__ == "__main__":
    if "--selfcheck" in sys.argv:
        selfcheck()
    else:
        main()
