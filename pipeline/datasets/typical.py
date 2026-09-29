"""Draw the typical-update pairs from the Wyss listings on the host; unpacking runs offline."""
import argparse

from pipeline.samples.extract import write_plan
from pipeline.samples.fetch import Fetcher
from pipeline.samples.listings import read_listing, write_listing
from pipeline.samples.registry import package_doc, update_has_advisory
from pipeline.shared.config import layout
from pipeline.shared.hashing import hash_order

TAKE_PER_LISTING = 50
LISTINGS = ("typical_updates_popular.txt", "typical_updates_random.txt")


# draw_typical takes pairs in hash order, replacing an update with an advisory by the next draw.
def draw_typical(entries, take, fetcher, out, skip_advisory=True, log=print):
    taken, reasons, plan = [], [], []
    for entry in hash_order(entries, key=lambda item: (item["name"], item["after"])):
        if len(taken) == take:
            break
        name, after = entry["name"], entry["after"]
        label = f"{name}@{after}"
        try:
            doc = package_doc(name)
        except Exception as exc:  # noqa: BLE001
            reasons.append((label, f"packument: {type(exc).__name__}"))
            continue
        if skip_advisory and update_has_advisory(name, after):
            reasons.append((label, "advisory"))
            continue
        rows, why = fetcher.plan(doc, entry, out)
        if why:
            reasons.append((label, why))
            continue
        taken.append(entry)
        plan.extend(rows)
        log(f"[{len(taken)}/{take}] {name}@{entry['before']} -> {after}")
    return taken, reasons, plan


def main(argv=None):
    data = layout()
    argparse.ArgumentParser(prog="typical").parse_args(argv)
    fetcher, kept, rejected, plan = Fetcher(data), [], [], []
    for listing in LISTINGS:
        print(f"--- {listing}")
        taken, reasons, rows = draw_typical(read_listing(data.wyss_listings / listing),
                                            TAKE_PER_LISTING, fetcher, data.typ)
        kept += taken
        rejected += reasons
        plan += rows
    write_listing(data.typ_taken, kept)
    write_plan(data.typ / "extract.plan.jsonl", plan)
    print(f"\n{data.typ_taken}: {len(kept)} pairs; extraction plan of {len(plan)} archives")
    for pair_id, why in rejected:
        print(f"  rejected {pair_id}: {why}")
