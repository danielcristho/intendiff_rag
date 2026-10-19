"""Select the malicious knowledge-base cards and hold every card to its size limit.

    python pipeline/kb.py select --pool data/mal_intent.jsonl --pairs data/pairs.jsonl --out data/kb.mal.jsonl
    python pipeline/kb.py fit --cards data/kb.jsonl --out data/kb.jsonl
    python pipeline/kb.py --selfcheck
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import capability  # noqa: E402
from collect import hash_key, hash_order  # noqa: E402
from prompts import card_block  # noqa: E402

CARD_BUDGET = 512
CODE_LINES = 15
MALICIOUS_CARDS = 50
PER_CAMPAIGN = 2

# The annotator fills these; selection only prepares the slots (§5.1).
WRITTEN_BY_HAND = ("intent", "behavior_chain", "code_excerpt", "rationale")


def load_jsonl(path):
    p = Path(path)
    if not p.exists():
        return []
    return [json.loads(line) for line in p.read_text().splitlines() if line.strip()]


def write_jsonl(path, rows):
    Path(path).write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows))


# with_delta gives a malicious-intent package its delta: the whole capability set,
# because such a package has no benign predecessor (§3.4).
def with_delta(entry):
    return dict(entry, delta=entry.get("delta") or capability.capabilities(Path(entry["dir"])))


def card_id(entry):
    return f"kb-mal-{hash_key(entry['name'], entry['version'])[:8]}"


def skeleton(entry, drawn_for):
    card = {"id": card_id(entry), "label": "malicious",
            "name": entry["name"], "version": entry["version"],
            "campaign": entry.get("campaign"), "source": entry.get("source", "datadog"),
            "delta": entry["delta"], "drawn_for": drawn_for, "dir": entry.get("dir")}
    card.update({field: "" for field in WRITTEN_BY_HAND})
    return card


# select walks the capabilities round-robin, each in hash order, until the quota
# is met (§3.4). A rejection is permanent — a campaign quota never shrinks and a
# package is never untaken — so one cursor per capability is enough.
def select(pool, excluded=(), limit=MALICIOUS_CARDS, per_campaign=PER_CAMPAIGN):
    ranked = {name: hash_order([entry for entry in pool if name in entry["delta"]],
                               key=lambda entry: (entry["name"], entry["version"]))
              for name in capability.CAPABILITIES}
    cursors = {name: 0 for name in capability.CAPABILITIES}
    excluded, taken, per = set(excluded), set(), {}
    cards = []

    while len(cards) < limit:
        drew = False
        for name in capability.CAPABILITIES:
            if len(cards) >= limit:
                break
            queue = ranked[name]
            while cursors[name] < len(queue):
                entry = queue[cursors[name]]
                cursors[name] += 1
                campaign = entry.get("campaign")
                if (entry["name"], entry["version"]) in taken or campaign in excluded:
                    continue
                if per.get(campaign, 0) >= per_campaign:
                    continue
                taken.add((entry["name"], entry["version"]))
                per[campaign] = per.get(campaign, 0) + 1
                cards.append(skeleton(entry, name))
                drew = True
                break
        if not drew:
            break
    return cards


# mal_campaigns lists the campaigns a card must not come from (§3.4).
def mal_campaigns(pairs):
    return {row.get("campaign") for row in pairs
            if row.get("subset") == "MAL" and row.get("campaign")}


# fit holds a card to §5.1: at most 15 excerpt lines, then 512 tokens, and the
# code excerpt is what gets trimmed.
def fit(card, count, budget=CARD_BUDGET, max_lines=CODE_LINES):
    card = dict(card)
    lines = str(card.get("code_excerpt") or "").splitlines()[:max_lines]
    card["code_excerpt"] = "\n".join(lines)

    # Stop at one line: an empty excerpt renders as the "not available" placeholder,
    # which is longer than a short line of code, so the last pop would grow the card.
    while count(card_block(1, card)) > budget and len(lines) > 1:
        lines.pop()
        card["code_excerpt"] = "\n".join(lines)
    return card, count(card_block(1, card)) <= budget


def main(argv=None):
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    pick = sub.add_parser("select", help="round-robin the malicious-intent pool into card slots")
    pick.add_argument("--pool", required=True, help="one line per malicious-intent package")
    pick.add_argument("--pairs", help="pairs.jsonl or its manifest, to exclude MAL campaigns")
    pick.add_argument("--limit", type=int, default=MALICIOUS_CARDS)
    pick.add_argument("--out", required=True)

    trim = sub.add_parser("fit", help="hold every card to the §5.1 size limit")
    trim.add_argument("--cards", required=True)
    trim.add_argument("--out", required=True)
    trim.add_argument("--budget", type=int, default=CARD_BUDGET)
    trim.add_argument("--approx", action="store_true",
                      help="count 4 characters per token instead of loading the tokenizer")

    args = parser.parse_args(argv)

    if args.command == "select":
        pool = [with_delta(entry) for entry in load_jsonl(args.pool)]
        excluded = mal_campaigns(load_jsonl(args.pairs)) if args.pairs else set()
        cards = select(pool, excluded, args.limit)
        write_jsonl(args.out, cards)
        per_capability = {name: sum(1 for card in cards if card["drawn_for"] == name)
                          for name in capability.CAPABILITIES}
        print(json.dumps({"cards": len(cards), "pool": len(pool),
                          "excluded_campaigns": len(excluded),
                          "drawn_for": per_capability}))
        return

    import smartdiff
    count = (lambda text: len(text) // 4) if args.approx else smartdiff.qwen_counter()
    fitted, oversized = [], []
    for card in load_jsonl(args.cards):
        card, ok = fit(card, count, args.budget)
        fitted.append(card)
        if not ok:
            oversized.append(card["id"])
    write_jsonl(args.out, fitted)
    print(json.dumps({"cards": len(fitted), "oversized": oversized}))


def selfcheck():
    count = lambda text: len(text) // 4  # noqa: E731 - the --approx counter

    pool = []
    for n in range(40):
        # Every package carries two capabilities, so the round-robin has to choose.
        pair = (capability.CAPABILITIES[n % 8], capability.CAPABILITIES[(n + 3) % 8])
        pool.append({"name": f"p{n}", "version": "1.0.0", "campaign": f"c{n // 3}",
                     "source": "datadog", "dir": f"/nonexistent/p{n}",
                     "delta": sorted(set(pair))})

    cards = select(pool, limit=12)
    assert len(cards) == 12

    # §3.4: at most two cards per campaign.
    per_campaign = {}
    for card in cards:
        per_campaign[card["campaign"]] = per_campaign.get(card["campaign"], 0) + 1
    assert max(per_campaign.values()) <= PER_CAMPAIGN, per_campaign

    # No package is used twice, and the draw is reproducible.
    assert len({card["id"] for card in cards}) == 12
    assert [card["id"] for card in select(list(reversed(pool)), limit=12)] == \
        [card["id"] for card in cards]

    # Round-robin: the first cards walk the capability table in order.
    assert [card["drawn_for"] for card in cards[:8]] == capability.CAPABILITIES

    # A campaign that also appears in MAL test is skipped entirely.
    pairs = [{"subset": "MAL", "campaign": "c0"}, {"subset": "HN", "campaign": "c1"}]
    assert mal_campaigns(pairs) == {"c0"}
    guarded = select(pool, excluded={"c0"}, limit=12)
    assert all(card["campaign"] != "c0" for card in guarded)

    # The annotator's fields are left empty, never invented.
    assert all(cards[0][field] == "" for field in WRITTEN_BY_HAND)

    # Package exclusions need the original identity, not the hashed card id.
    from runner import eligible
    assert not eligible({"name": cards[0]["name"], "campaign": "other"}, cards[0])
    assert eligible({"name": "unrelated-package", "campaign": "other"}, cards[0])
    assert cards[0]["version"] == "1.0.0"

    # A card's bookkeeping stays out of the prompt; its label is what does reach it
    # (§5.1), because that is what makes the example contrastive.
    written = dict(cards[0], intent="purpose", behavior_chain="chain",
                   code_excerpt="send(x)", rationale="why")
    rendered = card_block(1, written)
    for hidden in (written["id"], written["campaign"], written["source"],
                   written["drawn_for"], written["dir"], written["name"], written["version"]):
        assert hidden not in rendered, hidden
    assert "MALICIOUS" in rendered

    # §5.1: the excerpt is capped at 15 lines and trimmed until the card fits.
    long_card = {"id": "c", "label": "malicious", "intent": "x", "behavior_chain": "y",
                 "code_excerpt": "\n".join(f"line {n}" for n in range(40)),
                 "rationale": "z"}
    fitted, ok = fit(long_card, count)
    assert ok and len(fitted["code_excerpt"].splitlines()) <= CODE_LINES

    tight, ok = fit(long_card, count, budget=23)
    assert ok and len(tight["code_excerpt"].splitlines()) < CODE_LINES

    # Trimming never empties the excerpt, because the placeholder that replaces it
    # is longer than one line of code.
    assert tight["code_excerpt"].strip()
    assert not fit(long_card, count, budget=5)[0]["code_excerpt"].count("\n")

    # A card whose prose alone busts the budget is reported, not silently mangled.
    wordy = dict(long_card, rationale="word " * 400, code_excerpt="")
    _, ok = fit(wordy, count, budget=50)
    assert not ok

    print("ok")


if __name__ == "__main__":
    if "--selfcheck" in sys.argv:
        selfcheck()
    else:
        main()
