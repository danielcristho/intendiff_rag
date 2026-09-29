"""Assemble the dev set from Wyss malicious clones and unused typical updates."""
import argparse

from pipeline.datasets.pairs import assign_campaigns, build_row
from pipeline.datasets.typical import LISTINGS, draw_typical
from pipeline.features.files import package_root
from pipeline.samples.extract import write_plan
from pipeline.samples.fetch import Fetcher
from pipeline.samples.listings import listing_entry, read_listing, write_listing
from pipeline.shared.config import layout
from pipeline.shared.hashing import hash_key
from pipeline.shared.isolation import require_offline
from pipeline.shared.jsonl import read_jsonl, write_jsonl
from pipeline.shared.tokens import qwen_counter

# Consts
CLONES = 4
TYPICAL = 3


# read_clones parses malicious_clones.txt, whose after side is a bare directory used as the version.
def read_clones(path):
    entries = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        before_path, after_path = line.strip().split(",")
        name, before = listing_entry(before_path)
        entries.append({"name": name, "before": before, "after": after_path.rsplit("/", 1)[1],
                        "before_path": before_path, "after_path": after_path})
    return entries


def draw_clones(entries, take=CLONES):
    return sorted(entries, key=lambda entry: hash_key(entry["name"], entry["after"]))[:take]


# unused_typical drops every pair the typical test subset holds.
def unused_typical(listings, typ_pairs):
    taken = {row["id"] for row in read_jsonl(typ_pairs)}
    return [entry for listing in listings for entry in read_listing(listing)
            if f"{entry['name']}@{entry['after']}" not in taken]


def draw(data):
    listings = [data.wyss_listings / name for name in LISTINGS]
    typical, rejected, plan = draw_typical(unused_typical(listings, data.pairs_typ), TYPICAL,
                                           Fetcher(data), data.typ)
    for pair_id, why in rejected:
        print(f"  rejected {pair_id}: {why}")
    # HN path A excludes these, so a dev pair cannot come back as a test item.
    write_listing(data.dev_taken, typical)
    write_plan(data.typ / "dev.extract.plan.jsonl", plan)
    print(f"{data.dev_taken}: {len(typical)} typical pairs; extraction plan of {len(plan)} archives")


def build(data):
    require_offline()
    clones = draw_clones(read_clones(data.wyss_listings / "malicious_clones.txt"))
    count, rows, sides = qwen_counter(), [], []
    for entries, root, subset, source in ((clones, data.wyss_clones, "MAL", "wyss-osf-clone"),
                                          (read_listing(data.dev_taken), data.typ, "TYP", "wyss-typical")):
        for entry in entries:
            before, after = (package_root(root / entry[side]) for side in ("before_path", "after_path"))
            rows.append(build_row(entry["name"], entry["before"], entry["after"],
                                  before, after, subset, source, count))
            sides.append((before, after))
    assign_campaigns(rows, sides)
    write_jsonl(data.pairs_dev, rows)
    print(f"{data.pairs_dev}: {len(rows)} pairs ({len(clones)} clones)")
    # TODO: three hard negatives from the knowledge-base share, once the HN split exists.


def main(argv=None):
    parser = argparse.ArgumentParser(prog="devset")
    parser.add_argument("step", choices=("draw", "build"))
    args = parser.parse_args(argv)
    (draw if args.step == "draw" else build)(layout())
