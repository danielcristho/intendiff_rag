"""Statistical tests; statsmodels is the fixed implementation for the standard ones."""
from collections import defaultdict

import numpy as np

from pipeline.results.metrics import verdict_of

BOOTSTRAP_SEED = 2026
BOOTSTRAP_RESAMPLES = 10_000


def statsmodels(module):
    try:
        return __import__(module, fromlist=["*"])
    except ImportError as exc:  # pragma: no cover - depends on the host
        raise RuntimeError(f"statsmodels is required; {module} is unavailable") from exc


def wilson_ci(successes, total, alpha=0.05):
    if total == 0:
        return (0.0, 0.0)
    return statsmodels("statsmodels.stats.proportion").proportion_confint(successes, total, alpha=alpha,
                                                                          method="wilson")


# mcnemar_p is 1.0 when no pair is discordant, as there is nothing to test.
def mcnemar_p(only_baseline, only_variant):
    if only_baseline + only_variant == 0:
        return 1.0
    tables = statsmodels("statsmodels.stats.contingency_tables")
    return float(tables.mcnemar([[0, only_baseline], [only_variant, 0]], exact=True).pvalue)


def holm(pvalues, alpha=0.05):
    if not pvalues:
        return []
    return list(statsmodels("statsmodels.stats.multitest").multipletests(pvalues, alpha=alpha, method="holm")[1])


def cohens_kappa(table):
    return float(statsmodels("statsmodels.stats.inter_rater").cohens_kappa(np.asarray(table)).kappa)


# discordant returns McNemar's cells: pairs the baseline alone calls malicious, and those the variant alone does.
def discordant(baseline_rows, variant_rows, invalid_as="benign"):
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


# recall_delta_bootstrap resamples campaigns, not pairs, since pairs within a campaign are correlated.
def recall_delta_bootstrap(variant_rows, baseline_rows, pairs,
                           resamples=BOOTSTRAP_RESAMPLES, seed=BOOTSTRAP_SEED):
    members = defaultdict(list)
    for pair in pairs:
        members[pair.get("campaign") or pair["id"]].append(pair["id"])
    variant = {row["pair_id"]: verdict_of(row) for row in variant_rows}
    baseline = {row["pair_id"]: verdict_of(row) for row in baseline_rows}
    campaigns = sorted(members)
    if not campaigns:
        return 0.0, (0.0, 0.0)

    def recall_over(pair_ids, table):
        scored = [table[pid] for pid in pair_ids if pid in table]
        return sum(v == "malicious" for v in scored) / len(scored) if scored else 0.0

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
