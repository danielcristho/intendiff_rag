"""Hard-negative criteria shared by both collection paths."""
import collections
from pathlib import Path

from pipeline.features.capability import delta
from pipeline.features.files import has_content, package_root
from pipeline.samples.registry import publisher, update_has_advisory
from pipeline.shared.specs import hn_categories

CATEGORIES = hn_categories()


def matching_categories(signals):
    found = set(signals)
    return [number for number, spec in sorted(CATEGORIES.items()) if spec["signals"] & found]


# hn_rejection returns why an update fails the network-checked criteria, or None.
def hn_rejection(doc, name, before, after):
    if update_has_advisory(name, after):
        return "advisory"
    # A change of publisher is the takeover being detected, so it cannot be a benign example.
    who = [publisher(doc, version) for version in (before, after)]
    if all(who) and who[0] != who[1]:
        return f"publisher {who[0]} -> {who[1]}"
    return None


# pair_delta reads both extracted versions under out; returns (delta, None) or (None, reason).
def pair_delta(entry, out):
    roots = [package_root(Path(out) / entry[side]) for side in ("before_path", "after_path")]
    if not all(has_content(root) for root in roots):
        return None, "not extracted"
    return delta(*roots), None


def hn_candidate(entry, signals):
    return {**entry, "delta": signals, "categories": matching_categories(signals)}


# reason_kind groups rejection reasons; a publisher change names both publishers.
def reason_kind(why):
    return "publisher" if why.startswith("publisher") else why.split(":")[0]


def print_tally(rejected):
    for why, count in collections.Counter(reason_kind(why) for _, why in rejected).most_common():
        print(f"  {count:5}  rejected: {why}")
