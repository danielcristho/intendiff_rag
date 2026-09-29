"""Knowledge-base card retrieval: ranking by capability overlap, and each configuration's strategy."""
import hashlib
import zlib

from pipeline.shared.specs import configurations


# score is the Jaccard overlap of two capability deltas; text plays no part.
def score(pair_delta, card_delta):
    a, b = set(pair_delta or []), set(card_delta or [])
    union = a | b
    return len(a & b) / len(union) if union else 0.0


# eligible refuses a card from the same package or campaign, which would leak the answer.
def eligible(pair, card):
    return not any(pair.get(field) and pair.get(field) == card.get(field) for field in ("name", "campaign"))


# rank breaks score ties by hash, so the order of kb.jsonl cannot pick the winner.
def rank(pair, kb):
    def key(card):
        tiebreak = hashlib.sha256(f"{pair.get('id')}|{card.get('id')}".encode()).hexdigest()
        return (-score(pair.get("delta"), card.get("delta")), tiebreak)

    return sorted((card for card in kb if eligible(pair, card)), key=key)


# ordered puts the primary card first or second by the pair's hash, the same way in every strategy.
def ordered(pair_id, primary, secondary):
    if secondary is None:
        return [primary]
    return [primary, secondary] if zlib.crc32(str(pair_id).encode()) % 2 == 0 else [secondary, primary]


def nearest(pair, malicious, benign, ranked):
    return ranked[:1]


def one_malicious(pair, malicious, benign, ranked):
    return malicious[:1]


def two_malicious(pair, malicious, benign, ranked):
    return ordered(pair.get("id"), *(malicious[:2] + [None])[:2]) if malicious else []


# contrastive pairs the nearest malicious card with the nearest benign one.
def contrastive(pair, malicious, benign, ranked):
    if not malicious and not benign:
        return []
    primary = malicious[0] if malicious else benign[0]
    return ordered(pair.get("id"), primary, benign[0] if malicious and benign else None)


STRATEGIES = {"none": lambda *_: [], "nearest": nearest, "malicious": one_malicious,
              "two_malicious": two_malicious, "contrastive": contrastive}


# retrieve returns the cards one configuration is given, in prompt order.
def retrieve(config, pair, kb):
    strategy = configurations()[config]["cards"]
    if strategy == "none" or not kb:
        return []
    ranked = rank(pair, kb)
    malicious = [card for card in ranked if card.get("label") == "malicious"]
    benign = [card for card in ranked if card.get("label") == "benign"]
    return STRATEGIES[strategy](pair, malicious, benign, ranked)


def retrieval_log(pair, cards):
    return [{"id": card.get("id"), "label": card.get("label"),
             "score": round(score(pair.get("delta"), card.get("delta")), 4), "position": position}
            for position, card in enumerate(cards, start=1)]
