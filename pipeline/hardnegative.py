"""Split the verified hard negatives into the test subset and the benign card pool.

    python pipeline/hardnegative.py --verified data/hn_verified.jsonl \
        --test data/hn_test.jsonl --cards data/hn_cards.jsonl
    python pipeline/hardnegative.py --selfcheck
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from collect import SEED, HN_CATEGORIES, deterministic_draw, hash_order  # noqa: E402

TEST_PER_CATEGORY = 20
CARDS_PER_CATEGORY = 5
TEST_TOTAL = TEST_PER_CATEGORY * len(HN_CATEGORIES)
CARDS_TOTAL = CARDS_PER_CATEGORY * len(HN_CATEGORIES)


def load_jsonl(path):
    p = Path(path)
    if not p.exists():
        return []
    return [json.loads(line) for line in p.read_text().splitlines() if line.strip()]


def write_jsonl(path, rows):
    Path(path).write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows))


# by_category groups on the category the annotator assigned, never on the signal
# that screened the candidate (§3.3).
def by_category(verified):
    groups = {number: [] for number in sorted(HN_CATEGORIES)}
    unassigned = []
    for row in verified:
        if row.get("category") in groups:
            groups[row["category"]].append(row)
        else:
            unassigned.append(row)
    return groups, unassigned


# split_category fills the card quota before the test quota. The knowledge base
# needs one benign card per category for retrieval to have a look-alike at all,
# while a short test subset can still be topped up from another category (D60).
def split_category(entries, seed=SEED, cards=CARDS_PER_CATEGORY, test=TEST_PER_CATEGORY):
    for_cards, rest = deterministic_draw(entries, cards, seed)
    for_test, leftover = deterministic_draw(rest, test, seed)
    return for_cards, for_test, leftover


# backfill tops a short quota up from the leftovers of the categories that had a
# surplus, in hash order (D60). Ordering by digest rather than by category keeps
# category 1 from always being raided before category 2.
def backfill(chosen, leftovers, quota):
    queue = hash_order(leftovers, key=lambda row: (row["name"], row["version"]))
    while len(chosen) < quota and queue:
        chosen.append(queue.pop(0))
    return chosen, queue


def split(verified, seed=SEED):
    groups, unassigned = by_category(verified)

    cards, test, spare = [], [], []
    per_category = {}
    for number, entries in groups.items():
        for_cards, for_test, leftover = split_category(entries, seed)
        cards.extend(for_cards)
        test.extend(for_test)
        spare.extend(leftover)
        per_category[number] = {"available": len(entries),
                                "cards": len(for_cards), "test": len(for_test)}

    cards, spare = backfill(cards, spare, CARDS_TOTAL)
    test, spare = backfill(test, spare, TEST_TOTAL)

    for row in cards:
        row["portion"] = "kb"
    for row in test:
        row["portion"] = "test"

    return {"cards": cards, "test": test, "spare": spare,
            "per_category": per_category, "unassigned": len(unassigned)}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--verified", required=True,
                        help="verified hard negatives, each with the annotator's category")
    parser.add_argument("--test", required=True)
    parser.add_argument("--cards", required=True)
    parser.add_argument("--spare", help="candidates neither quota needed")
    args = parser.parse_args(argv)

    result = split(load_jsonl(args.verified))
    write_jsonl(args.test, result["test"])
    write_jsonl(args.cards, result["cards"])
    if args.spare:
        write_jsonl(args.spare, result["spare"])

    short = {number: counts for number, counts in result["per_category"].items()
             if counts["test"] < TEST_PER_CATEGORY or counts["cards"] < CARDS_PER_CATEGORY}
    print(json.dumps({"test": len(result["test"]), "cards": len(result["cards"]),
                      "spare": len(result["spare"]), "unassigned": result["unassigned"],
                      "short_of_quota": short, "per_category": result["per_category"]}))


def selfcheck():
    def candidates(category, count, tag=""):
        return [{"name": f"{tag}pkg{category}-{n}", "version": "1.0.0", "category": category}
                for n in range(count)]

    # Every category at quota: the split is exactly 20 test and 5 cards each.
    full = [row for number in HN_CATEGORIES for row in candidates(number, 25)]
    result = split(full)
    assert len(result["test"]) == TEST_TOTAL and len(result["cards"]) == CARDS_TOTAL
    assert result["spare"] == []
    assert all(counts == {"available": 25, "cards": 5, "test": 20}
               for counts in result["per_category"].values())

    # Nothing is used twice, and the two portions are disjoint.
    names = [row["name"] for row in result["test"] + result["cards"]]
    assert len(names) == len(set(names)) == TEST_TOTAL + CARDS_TOTAL
    assert result["test"][0]["portion"] == "test" and result["cards"][0]["portion"] == "kb"

    # Reproducible, and the input order cannot change the split.
    again = split(list(reversed(full)))
    assert [row["name"] for row in again["test"]] == [row["name"] for row in result["test"]]
    assert [row["name"] for row in split(full, seed=1)["test"]] != \
        [row["name"] for row in result["test"]]

    # D60: a short category keeps its benign card, and the test total is topped up
    # from the categories that had a surplus.
    lean = candidates(3, 8, "lean-") + [row for number in (1, 2, 4, 5)
                                        for row in candidates(number, 40)]
    patched = split(lean)
    assert len(patched["test"]) == TEST_TOTAL, len(patched["test"])
    assert len(patched["cards"]) == CARDS_TOTAL
    assert patched["per_category"][3] == {"available": 8, "cards": 5, "test": 3}
    assert sum(1 for row in patched["cards"] if row["category"] == 3) == 5

    # A category with fewer candidates than the card quota gives what it has.
    scarce = candidates(3, 2, "scarce-") + [row for number in (1, 2, 4, 5)
                                            for row in candidates(number, 40)]
    thin = split(scarce)
    assert thin["per_category"][3] == {"available": 2, "cards": 2, "test": 0}
    assert len(thin["cards"]) == CARDS_TOTAL, "the shortfall comes from the surplus"

    # A candidate the annotator never categorised is counted, never guessed into place.
    counted = split(full + [{"name": "loose", "version": "1.0.0"}])
    assert counted["unassigned"] == 1
    assert "loose" not in [row["name"] for row in counted["test"] + counted["cards"]]

    print("ok")


if __name__ == "__main__":
    if "--selfcheck" in sys.argv:
        selfcheck()
    else:
        main()
