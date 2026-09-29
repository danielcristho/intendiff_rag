from pipeline.results.comparisons import outcome, wording
from pipeline.results.metrics import (evidence_localization, flip_rate, json_validity, latest_runs,
                                      percentile_nearest_rank, rate, subset_rows, verdict_of)
from pipeline.results.statistics import discordant, mcnemar_p, recall_delta_bootstrap

PAIRS = [{"id": "m1", "subset": "MAL", "campaign": "c1", "gold_evidence": ["+  eval(payload);"]},
         {"id": "m2", "subset": "MAL", "campaign": "c1"}, {"id": "h1", "subset": "HN", "campaign": "c2"},
         {"id": "h2", "subset": "HN", "campaign": "c3"}, {"id": "t1", "subset": "TYP", "campaign": "c4"}]


def row(pair_id, config, verdict, **extra):
    return {"pair_id": pair_id, "config": config, "model": "m", "verdict": verdict,
            "json_valid": extra.pop("json_valid", True), **extra}


def test_an_invalid_reply_counts_as_benign_unless_the_sensitivity_run_says_malicious():
    broken = row("p1", "E0", None, json_valid=False)
    assert verdict_of(broken) == "benign" and verdict_of(broken, "malicious") == "malicious"
    assert verdict_of(row("p1", "E0", "suspicious")) == "benign"


def test_rates_are_shares_called_malicious_per_subset():
    rows = [row("m1", "E0", "malicious"), row("m2", "E0", "benign"), row("h1", "E0", "malicious"),
            row("h2", "E0", "benign"), row("t1", "E0", "benign")]
    assert rate(subset_rows(rows, PAIRS, "MAL")) == 0.5 and rate(subset_rows(rows, PAIRS, "TYP")) == 0.0
    assert rate([]) == 0.0 and json_validity(rows) == 1.0


def test_evidence_matches_either_way_and_needs_gold_lines():
    assert evidence_localization([row("m1", "E0", "malicious", evidence=["+   eval(payload);"])], PAIRS) == 1.0
    assert evidence_localization([row("m1", "E0", "malicious", evidence=["+  require('fs');"])], PAIRS) == 0.0
    assert evidence_localization([row("m2", "E0", "malicious", evidence=["x"])], PAIRS) == 0.0


def test_stability_counts_pairs_and_latency_uses_nearest_rank():
    assert flip_rate([row("p1", "E0", "benign")] * 2) == 0.0
    assert flip_rate([row("p1", "E0", "benign"), row("p1", "E0", "malicious")]) == 1.0
    assert percentile_nearest_rank(list(range(1, 11)), 0.95) == 10 and percentile_nearest_rank([], 0.5) == 0.0


def test_mcnemar_uses_only_discordant_pairs():
    baseline = [row("h1", "E0", "malicious"), row("h2", "E0", "malicious")]
    variant = [row("h1", "E4", "benign"), row("h2", "E4", "malicious")]
    assert discordant(baseline, variant) == (1, 0) and discordant(variant, baseline) == (0, 1)
    assert mcnemar_p(0, 0) == 1.0


def test_the_bootstrap_resamples_campaigns_and_reproduces_with_its_seed():
    mal = [p for p in PAIRS if p["subset"] == "MAL"]
    better = [row("m1", "E4", "malicious"), row("m2", "E4", "malicious")]
    worse = [row("m1", "E0", "malicious"), row("m2", "E0", "benign")]
    delta, (low, high) = recall_delta_bootstrap(better, worse, mal, resamples=200)
    assert abs(delta - 50.0) < 1e-6 and low <= delta <= high
    assert recall_delta_bootstrap(worse, worse, mal, resamples=200) == (0.0, (0.0, 0.0))
    assert recall_delta_bootstrap(better, worse, mal, resamples=200)[0] == delta


def test_only_the_last_attempt_of_a_run_counts():
    attempts = [{"run_key": "k1", "pair_id": "h1", "json_valid": False, "error": "reset"},
                {"run_key": "k1", "pair_id": "h1", "verdict": "benign", "json_valid": True},
                {"run_key": "k2", "pair_id": "h2", "verdict": "benign", "json_valid": True}]
    kept = latest_runs(attempts)
    assert len(kept) == 2 and json_validity(kept) == 1.0 and latest_runs(kept) == kept


def test_each_outcome_key_follows_direction_significance_and_the_recall_guard():
    assert outcome(True, 0.01, -1.0, -3.0, True) == "confirmed"
    assert outcome(True, 0.01, -1.0, -9.0, True) == "confirmed_point_only"
    assert outcome(True, 0.30, -1.0, -3.0, True) == "not_significant"
    assert outcome(False, 0.01, -1.0, -3.0, True) == "not_moved"
    assert outcome(True, 0.001, -7.0, -9.0, True) == "recall_drop"
    assert outcome(True, 0.01, -40.0, -60.0, False) == "confirmed"
    assert all(wording(key) for key in ("confirmed", "confirmed_point_only", "not_significant", "not_moved", "recall_drop"))
