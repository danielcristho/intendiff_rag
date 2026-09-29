"""Select the malicious knowledge-base cards: fetch on the host, select offline."""
import argparse
import sys
import tempfile
from pathlib import Path

from pipeline.datasets.kb.cards import TEXT_FIELDS
from pipeline.datasets.kb.datadog import NotFetched, extracted_root, fetch_samples, pool
from pipeline.features import capability
from pipeline.features.campaign import added_hashes, cluster
from pipeline.features.files import has_content, package_root
from pipeline.features.signals import CAPABILITIES
from pipeline.samples.extract import write_plan
from pipeline.samples.listings import read_listing
from pipeline.shared.config import layout
from pipeline.shared.isolation import require_offline
from pipeline.shared.jsonl import read_jsonl, write_jsonl

TOTAL_CARDS = 50
PER_CAMPAIGN = 2


# mal_hashes collects the added-file digests of every malicious test pair, to keep their campaigns out.
def mal_hashes(listing, roots, empty):
    digests = set()
    for entry in read_listing(listing):
        before, after = (package_root(roots / entry[side]) for side in ("before_path", "after_path"))
        if has_content(before) and has_content(after):
            digests |= added_hashes(before, after)
    return digests


# linked_cards returns the chosen cards a candidate would join by transitive closure.
def linked_cards(hashes, chosen):
    linked, frontier, grew = set(), set(hashes), True
    while grew:
        grew = False
        for card in chosen:
            if card["id"] not in linked and card["hashes"] & frontier:
                linked.add(card["id"])
                frontier |= card["hashes"]
                grew = True
    return linked


# select fills the cards round-robin over the capabilities in table order.
def select(entries, scan, test_hashes, total=TOTAL_CARDS, log=print):
    chosen, cursors, exhausted, taken = [], dict.fromkeys(CAPABILITIES, 0), set(), set()
    skipped = {"mal_campaign": set(), "campaign_full": set(), "unreadable": set()}
    while len(chosen) < total and len(exhausted) < len(CAPABILITIES):
        for wanted in CAPABILITIES:
            if len(chosen) >= total or wanted in exhausted:
                continue
            while cursors[wanted] < len(entries):
                entry = entries[cursors[wanted]]
                cursors[wanted] += 1
                key = f"{entry['name']}@{entry['version']}"
                if key in taken:
                    continue
                found = scan(entry)
                if found is None:
                    skipped["unreadable"].add(key)
                elif wanted not in found["delta"]:
                    continue
                elif found["hashes"] & test_hashes:
                    skipped["mal_campaign"].add(key)
                elif len(linked_cards(found["hashes"], chosen)) >= PER_CAMPAIGN:
                    skipped["campaign_full"].add(key)
                else:
                    taken.add(key)
                    chosen.append({"id": f"kb-mal-{key}", "entry": entry, "wanted": wanted, **found})
                    break
            else:
                exhausted.add(wanted)
                log(f"capability {wanted} exhausted after {len(chosen)} cards")
    # Counted per sample, since every capability pass revisits the same pool.
    return chosen, {reason: len(keys) for reason, keys in skipped.items()}


# skeleton turns a chosen card into a row whose text an annotator writes from the sample's code.
def skeleton(card, campaign_id):
    row = {"id": card["id"], "name": card["entry"]["name"], "label": "malicious", "campaign": campaign_id,
           "source": "datadog", "delta": card["delta"], "selected_for": card["wanted"],
           "root": card["root"], "delta_evidence": card["evidence"]}
    row.update(dict.fromkeys(TEXT_FIELDS, ""))
    return row


def assign_campaigns(chosen):
    return cluster([{"id": card["id"], "reports": [], "added_hashes": card["hashes"]} for card in chosen])


def run_fetch(data, count):
    entries = pool(data.datadog)
    write_jsonl(data.datadog / "pool.jsonl", entries)
    plan = fetch_samples(data.datadog, entries, count)
    write_plan(data.datadog / "extract.plan.jsonl", plan)
    print(f"pool: {len(entries)} malicious-intent samples; {len(plan)} fetched")


def run_select(data):
    require_offline()
    empty = Path(tempfile.mkdtemp())
    test_hashes = mal_hashes(data.wyss_listings / "malicious_updates.txt", data.wyss_mal, empty)
    entries = read_jsonl(data.datadog / "pool.jsonl")
    print(f"pool: {len(entries)} malicious-intent samples; test-pair digests: {len(test_hashes)}")
    scanned = {}

    def scan(entry):
        key = (entry["name"], entry["version"])
        if key not in scanned:
            root = extracted_root(data.datadog, entry)
            scanned[key] = None if root is None else {
                "root": root.relative_to(data.root).as_posix(),
                "delta": capability.capabilities(root),
                "evidence": capability.explain_version(root),
                "hashes": added_hashes(empty, root),
            }
        return scanned[key]

    try:
        chosen, skipped = select(entries, scan, test_hashes)
    except NotFetched as missing:
        sys.exit(f"selection reached {missing}, which is not fetched; rerun the fetch with a larger count")
    labels = assign_campaigns(chosen)
    write_jsonl(data.kb_skeleton, [skeleton(card, labels[card["id"]]) for card in chosen])
    print(f"{data.kb_skeleton}: {len(chosen)} cards, {len(set(labels.values()))} campaigns, "
          f"{len(scanned)} samples scanned")
    print(f"skipped: {skipped}")
    print(f"cards per capability: { {name: sum(name in c['delta'] for c in chosen) for name in CAPABILITIES} }")


def main(argv=None):
    parser = argparse.ArgumentParser(prog="kb")
    parser.add_argument("step", choices=("fetch", "select"))
    parser.add_argument("--count", type=int, default=600, help="pool samples to fetch, in hash order")
    args = parser.parse_args(argv)
    data = layout()
    if args.step == "fetch":
        run_fetch(data, args.count)
    else:
        run_select(data)
