"""Paired configuration comparisons, defined in pipeline/specs/comparisons.json."""
from pipeline.shared.specs import load_spec

SPEC = load_spec("comparisons")
ALPHA, RECALL_GUARD = SPEC["alpha"], SPEC["recall_guard_pt"]
COMPARISONS = {entry["name"]: entry for entry in SPEC["comparisons"]}


def moved_as_expected(entry, fpr_baseline, fpr_variant):
    return fpr_variant > fpr_baseline if entry["direction"] == "up" else fpr_variant < fpr_baseline


# outcome turns the test results into a neutral key; the spec maps each key to its wording.
def outcome(moved, p_holm, recall_delta, recall_low, guarded):
    if not moved:
        return "not_moved"
    if guarded and recall_delta < RECALL_GUARD:
        return "recall_drop"
    if p_holm >= ALPHA:
        return "not_significant"
    if not guarded or recall_low >= RECALL_GUARD:
        return "confirmed"
    return "confirmed_point_only"


def wording(key):
    return SPEC["outcomes"][key]
