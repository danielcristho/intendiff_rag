"""Per-configuration measures over result rows: rates, validity, evidence, stability and cost."""
import math
import re
from collections import defaultdict

WHITESPACE = re.compile(r"\s+")


# latest_runs keeps the last row per run_key, since a retried run appends instead of replacing.
def latest_runs(rows):
    newest = {}
    for row in rows:
        newest[row.get("run_key") or id(row)] = row
    return list(newest.values())


# verdict_of counts an invalid reply as `invalid_as`: benign in the main analysis.
def verdict_of(row, invalid_as="benign"):
    if not row.get("json_valid") or row.get("verdict") not in ("malicious", "benign"):
        return invalid_as
    return row["verdict"]


def subset_rows(rows, pairs, subset):
    members = {pair["id"] for pair in pairs if pair.get("subset") == subset}
    return [row for row in rows if row["pair_id"] in members]


# rate is the share called malicious: recall on malicious pairs, a false positive rate elsewhere.
def rate(rows, invalid_as="benign"):
    return sum(verdict_of(row, invalid_as) == "malicious" for row in rows) / len(rows) if rows else 0.0


def json_validity(rows):
    return sum(1 for row in rows if row.get("json_valid")) / len(rows) if rows else 0.0


def normalise(text):
    return WHITESPACE.sub(" ", str(text)).strip()


# evidence_hits_gold matches a substring either way once whitespace is normalised.
def evidence_hits_gold(row, gold_lines):
    for item in row.get("evidence") or ():
        candidate = normalise(item)
        if candidate and any((reference := normalise(gold)) and (candidate in reference or reference in candidate)
                             for gold in gold_lines):
            return True
    return False


# evidence_localization is measured over the rows called malicious.
def evidence_localization(rows, pairs, invalid_as="benign"):
    gold = {pair["id"]: pair.get("gold_evidence") or [] for pair in pairs}
    positives = [row for row in rows if verdict_of(row, invalid_as) == "malicious"]
    if not positives:
        return 0.0
    return sum(evidence_hits_gold(row, gold.get(row["pair_id"], [])) for row in positives) / len(positives)


# flip_rate is the share of pairs whose verdict differs across seeds.
def flip_rate(rows, invalid_as="benign"):
    by_pair = defaultdict(set)
    for row in rows:
        by_pair[row["pair_id"]].add(verdict_of(row, invalid_as))
    return sum(len(seen) > 1 for seen in by_pair.values()) / len(by_pair) if by_pair else 0.0


# percentile_nearest_rank uses nearest rank; numpy.percentile interpolates.
def percentile_nearest_rank(values, fraction):
    if not values:
        return 0.0
    ordered = sorted(values)
    return ordered[min(max(1, math.ceil(fraction * len(ordered))), len(ordered)) - 1]


def cost_summary(rows):
    def present(key):
        return [row[key] for row in rows if row.get(key) is not None]

    latencies, prompt, completion = present("latency_ms"), present("prompt_tokens"), present("completion_tokens")
    return {"median_latency_ms": percentile_nearest_rank(latencies, 0.5),
            "p95_latency_ms": percentile_nearest_rank(latencies, 0.95),
            "mean_prompt_tokens": sum(prompt) / len(prompt) if prompt else 0.0,
            "mean_completion_tokens": sum(completion) / len(completion) if completion else 0.0}
