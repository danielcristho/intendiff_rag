"""Prepare combined campaign inputs from acquired MAL and KB candidates.

    python pipeline/campaign_materials.py --acquisition DIR --out FILE
    python pipeline/campaign_materials.py --review FILE [FILE ...] --out FILE
"""
import argparse
import hashlib
import json
from pathlib import Path

import campaign
from samples import load_jsonl


# material treats a card (no before) as adding every file it ships. Trivial
# files are kept apart so the pre-D96 rule can still be reported.
def material(identity, role, before, after, reports):
    existing = {p.relative_to(before).as_posix() for p in before.rglob("*") if p.is_file()} if before else set()
    hashes, trivial, sources = [], [], []
    for path in sorted(after.rglob("*")):
        if not path.is_file() or path.relative_to(after).as_posix() in existing:
            continue
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        (trivial if campaign.is_trivial_file(raw) else hashes).append(digest)
        if path.suffix in campaign.SOURCE_SUFFIXES:
            text = campaign.read_text(path)
            if text is not None:
                sources.append(text)
    return {"id": identity, "role": role, "reports": reports,
            "added_hashes": sorted(set(hashes)), "trivial_hashes": sorted(set(trivial)),
            "code": "\n".join(sources)}


def acquisition_rows(args):
    root = Path(args.acquisition)
    pairs = load_jsonl(root / "mal.audit.jsonl") + load_jsonl(root / "datadog.pairs-screened.jsonl")
    inventory = {r["id"]: r for r in load_jsonl(root / args.inventory)}
    cards = [r for r in inventory.values() if r["kind"] == "malicious_intent" and not r.get("error")]
    advisories = {(r["name"], r["version"]): r for r in load_jsonl(root / args.advisories)}
    for row in pairs + cards:
        is_card = "before_dir" not in row
        before = None if is_card else Path(row["before_dir"])
        after = Path(row["dir"] if is_card else row["after_dir"])
        advisory = row.get("advisory_after") or advisories.get((row["name"], row.get("after", row.get("version"))), {})
        reports = [key for key in advisory.get("advisory_ids", []) if key.startswith("MAL-")]
        yield row["id"], "kb_pool" if is_card else "mal_candidate", before, after, reports


# review_rows keeps one item per pair id; TYP rows that are also HN candidates appear in both files.
def review_rows(paths):
    seen = set()
    for path in paths:
        for row in load_jsonl(path):
            if row["id"] in seen:
                continue
            seen.add(row["id"])
            role = "review_" + row["subset"].lower()
            yield row["id"], role, Path(row["before_dir"]), Path(row["after_dir"]), []


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--acquisition")
    parser.add_argument("--review", nargs="+")
    parser.add_argument("--out", required=True)
    parser.add_argument("--inventory", default="datadog.inventory.jsonl")
    parser.add_argument("--advisories", default="campaign-advisories.jsonl")
    args = parser.parse_args()
    if bool(args.acquisition) == bool(args.review):
        parser.error("pass exactly one of --acquisition or --review")
    rows = list(review_rows(args.review) if args.review else acquisition_rows(args))
    with Path(args.out).open("w") as output:
        for index, row in enumerate(rows, 1):
            output.write(json.dumps(material(*row)) + "\n")
            output.flush()
            if index % 100 == 0 or index == len(rows):
                print(f"campaign material {index}/{len(rows)}", flush=True)


if __name__ == "__main__":
    main()
