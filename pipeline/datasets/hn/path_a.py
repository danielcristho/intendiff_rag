"""Hard-negative path A: screen the unused Wyss typical updates, host step then offline step."""
import argparse
import collections

from pipeline.datasets.hn.rules import hn_candidate, hn_rejection, pair_delta, print_tally
from pipeline.datasets.typical import LISTINGS
from pipeline.samples.extract import write_plan
from pipeline.samples.fetch import Fetcher
from pipeline.samples.listings import read_listing
from pipeline.samples.registry import package_doc, publisher
from pipeline.shared.config import layout
from pipeline.shared.hashing import hash_order
from pipeline.shared.isolation import require_offline
from pipeline.shared.jsonl import read_jsonl, write_jsonl


# prefilter applies the network-checked criteria and fetches the tarballs of every survivor.
def prefilter(entries, fetcher, out, log=print):
    kept, reasons, plan = [], [], []
    for entry in hash_order(entries, key=lambda item: (item["name"], item["after"])):
        label = f"{entry['name']}@{entry['after']}"
        try:
            doc = package_doc(entry["name"])
        except Exception as exc:  # noqa: BLE001
            reasons.append((label, f"packument: {type(exc).__name__}"))
            continue
        why = hn_rejection(doc, entry["name"], entry["before"], entry["after"])
        rows = None
        if not why:
            rows, why = fetcher.plan(doc, entry, out)
        if why:
            reasons.append((label, why))
            continue
        kept.append({**entry, "publisher": publisher(doc, entry["after"])})
        plan.extend(rows)
        if len(kept) % 100 == 0:
            log(f"  {len(kept)} passed the criteria")
    return kept, reasons, plan


# screen keeps the prefiltered entries whose extracted versions show a non-empty delta.
def screen(entries, out):
    kept, reasons = [], []
    for entry in entries:
        signals, why = pair_delta(entry, out)
        if why or not signals:
            reasons.append((f"{entry['name']}@{entry['after']}", why or "empty delta"))
            continue
        kept.append(hn_candidate(entry, signals))
    return kept, reasons


def run_prefilter(data):
    spoken_for = {e["after_path"] for path in (data.typ_taken, data.dev_taken) for e in read_listing(path)}
    pool = [e for name in LISTINGS for e in read_listing(data.wyss_listings / name)
            if e["after_path"] not in spoken_for]
    print(f"path A: {len(pool)} pairs after removing {len(spoken_for)} already used")
    kept, rejected, plan = prefilter(pool, Fetcher(data), data.hn)
    write_jsonl(data.hn / "prefiltered.jsonl", kept)
    write_plan(data.hn / "extract.plan.jsonl", plan)
    print(f"\n{data.hn / 'prefiltered.jsonl'}: {len(kept)} pairs passed; {len(plan)} archives")
    print_tally(rejected)


def run_screen(data):
    require_offline()
    kept, rejected = screen(read_jsonl(data.hn / "prefiltered.jsonl"), data.hn)
    write_jsonl(data.hn / "candidates.jsonl", kept)
    print(f"{data.hn / 'candidates.jsonl'}: {len(kept)} candidates")
    print_tally(rejected)
    per_category = collections.Counter(c for entry in kept for c in entry["categories"])
    print("  signals matching each category:", dict(sorted(per_category.items())))


def main(argv=None):
    parser = argparse.ArgumentParser(prog="hn-path-a")
    parser.add_argument("step", choices=("prefilter", "screen"))
    args = parser.parse_args(argv)
    (run_prefilter if args.step == "prefilter" else run_screen)(layout())
