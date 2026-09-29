"""Build pair rows from extracted version directories, and merge the subsets into pairs.jsonl."""
import argparse
import sys

from pipeline.features import capability, intent, smartdiff
from pipeline.features.campaign import added_hashes, cluster
from pipeline.features.files import has_content, package_root
from pipeline.samples.listings import read_listing
from pipeline.shared.config import layout
from pipeline.shared.hashing import tree_digest
from pipeline.shared.isolation import require_offline
from pipeline.shared.jsonl import read_jsonl, write_jsonl
from pipeline.shared.tokens import qwen_counter


# PAIR_SETS describes each subset built from a listing; a new subset is a new entry.
def pair_sets(data):
    return {
        "mal": {"listing": data.wyss_listings / "malicious_updates.txt", "roots": data.wyss_mal,
                "subset": "MAL", "source": "wyss-osf", "out": data.pairs_mal},
        "typ": {"listing": data.typ_taken, "roots": data.typ,
                "subset": "TYP", "source": "wyss-typical", "out": data.pairs_typ},
    }


# build_row assembles one pair row; the intent comes from the previous version.
def build_row(name, before_version, after_version, before, after, subset, source, count):
    profile = intent.build(before, count)
    diff = smartdiff.build(before, after, count)
    return {
        "id": f"{name}@{after_version}", "name": name,
        "before": before_version, "after": after_version,
        "subset": subset, "category": None, "campaign": None, "source": source,
        "published_at": None,
        # The digests cover the unpacked trees, since some sources ship trees rather than tarballs.
        "sha256_before": tree_digest(before), "sha256_after": tree_digest(after),
        "intent": profile, "intent_available": intent.available(profile), "intent_from": before_version,
        "delta": capability.delta(before, after),
        "delta_evidence": capability.delta_evidence(before, after),
        "diff": diff["diff"], "truncated": diff["truncated"],
        "label": "malicious" if subset == "MAL" else "benign",
        # gold_evidence is annotated by hand, not derived from the extractor.
        "gold_evidence": [],
    }


# assign_campaigns clusters rows in place by shared reports and identical added files.
def assign_campaigns(rows, sides):
    items = [{"id": row["id"], "reports": [], "added_hashes": added_hashes(before, after), "code": ""}
             for row, (before, after) in zip(rows, sides)]
    labels = cluster(items)
    for row in rows:
        row["campaign"] = labels[row["id"]]


# build_pairs skips an entry with an empty side, which would read as a whole new package.
def build_pairs(entries, roots, subset, source, count):
    rows, sides, skipped = [], [], []
    for entry in entries:
        before, after = (package_root(roots / entry[side]) for side in ("before_path", "after_path"))
        if not all(side.is_dir() and has_content(side) for side in (before, after)):
            skipped.append(f"{entry['name']}@{entry['after']}")
            continue
        rows.append(build_row(entry["name"], entry["before"], entry["after"],
                              before, after, subset, source, count))
        sides.append((before, after))
    assign_campaigns(rows, sides)
    return rows, skipped


def merge(data):
    rows = [row for path in (data.pairs_mal, data.pairs_typ, data.pairs_hn) for row in read_jsonl(path)]
    write_jsonl(data.pairs, rows)
    print(f"{data.pairs}: {len(rows)} pairs")


def main(argv=None):
    data = layout()
    parser = argparse.ArgumentParser(prog="pairs")
    parser.add_argument("set", choices=[*pair_sets(data), "merge"])
    args = parser.parse_args(argv)
    if args.set == "merge":
        return merge(data)
    require_offline()
    spec = pair_sets(data)[args.set]
    rows, skipped = build_pairs(read_listing(spec["listing"]), spec["roots"], spec["subset"],
                                spec["source"], qwen_counter())
    if not rows:
        sys.exit(f"no pair built from {spec['listing']}; were the archives extracted?")
    write_jsonl(spec["out"], rows)
    print(f"{spec['out']}: {len(rows)} pairs, {len({r['campaign'] for r in rows})} campaigns, "
          f"{sum(r['truncated'] for r in rows)} truncated, "
          f"{sum(not r['intent_available'] for r in rows)} without intent")
    if skipped:
        print(f"skipped ({len(skipped)}): {', '.join(skipped[:5])}")
