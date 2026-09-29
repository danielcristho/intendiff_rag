"""The experimental configuration matrix.

    python pipeline/configs.py --selfcheck
"""
from typing import NamedTuple


class Config(NamedTuple):
    intent: bool
    cards: tuple


# §10. An ID spells out its factors: DIFF smart-diff, I intent block, M malicious
# card, B benign card (D62). A new configuration is a new row here, not a branch.
CONFIGS = {
    "DIFF": Config(intent=False, cards=()),
    "DIFF+I": Config(intent=True, cards=()),
    "DIFF+I+M": Config(intent=True, cards=("malicious",)),
    "DIFF+I+MM": Config(intent=True, cards=("malicious", "malicious")),
    "DIFF+I+MB": Config(intent=True, cards=("malicious", "benign")),
    "DIFF+MB": Config(intent=False, cards=("malicious", "benign")),
}

# The confirmatory contrasts (§10), each differing in exactly one factor.
CONTRASTS = (
    ("DIFF+I", "DIFF+I+M"),
    ("DIFF+I+MM", "DIFF+I+MB"),
    ("DIFF+MB", "DIFF+I+MB"),
)

# Superseded ids, kept so a stale caller fails loudly instead of silently
# retrieving nothing: E1 went with D8, E2 with D61, the rest renamed by D62.
RETIRED = ("E0-noint", "E0", "E1", "E2", "E3", "E3-k2", "E4", "E4-noint")


def spec(config):
    if config in RETIRED:
        raise ValueError(f"configuration {config} was retired; see decisions D8, D61, D62")
    if config not in CONFIGS:
        raise ValueError(f"unknown configuration: {config}")
    return CONFIGS[config]


def selfcheck():
    for baseline, variant in CONTRASTS:
        differs = (spec(baseline).intent != spec(variant).intent) + (
            spec(baseline).cards != spec(variant).cards
        )
        assert differs == 1, f"{baseline} vs {variant} differs in {differs} factors"

    # RQ2b only separates the contrastive effect from example count if both
    # sides carry the same number of cards.
    assert len(spec("DIFF+I+MM").cards) == len(spec("DIFF+I+MB").cards)

    # The intent ablation must not disturb retrieval.
    assert spec("DIFF+MB").cards == spec("DIFF+I+MB").cards

    for retired in RETIRED:
        try:
            spec(retired)
        except ValueError:
            continue
        raise AssertionError(f"{retired} must be rejected")

    print("ok")


if __name__ == "__main__":
    selfcheck()
