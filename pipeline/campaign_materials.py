"""Prepare combined campaign inputs from acquired MAL and KB candidates.

    python pipeline/campaign_materials.py --acquisition DIR --out FILE
"""
import argparse
import hashlib
import json
from pathlib import Path

import campaign
from samples import load_jsonl


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--acquisition", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--inventory", default="datadog.inventory.jsonl")
    parser.add_argument("--advisories", default="campaign-advisories.jsonl")
    args = parser.parse_args()
    root = Path(args.acquisition)
    pairs = load_jsonl(root / "mal.audit.jsonl") + load_jsonl(root / "datadog.pairs-screened.jsonl")
    inventory = {r["id"]: r for r in load_jsonl(root / args.inventory)}
    cards = [r for r in inventory.values() if r["kind"] == "malicious_intent" and not r.get("error")]
    advisories = {(r["name"], r["version"]): r for r in load_jsonl(root / args.advisories)}
    with Path(args.out).open("w") as output:
        for index, row in enumerate(pairs + cards, 1):
            is_card = "before_dir" not in row
            if is_card:
                after, before = Path(row["dir"]), None
            else:
                before, after = Path(row["before_dir"]), Path(row["after_dir"])
            existing = {p.relative_to(before).as_posix() for p in before.rglob("*") if p.is_file()} if before else set()
            hashes, sources = [], []
            for path in sorted(after.rglob("*")):
                if not path.is_file() or path.relative_to(after).as_posix() in existing:
                    continue
                with path.open("rb") as stream:
                    hashes.append(hashlib.file_digest(stream, "sha256").hexdigest())
                if path.suffix in campaign.SOURCE_SUFFIXES:
                    text = campaign.read_text(path)
                    if text is not None:
                        sources.append(text)
            advisory = row.get("advisory_after") or advisories.get((row["name"], row.get("after", row.get("version"))), {})
            reports = [key for key in advisory.get("advisory_ids", []) if key.startswith("MAL-")]
            result = {"id": row["id"], "role": "kb_pool" if is_card else "mal_candidate",
                      "reports": reports, "added_hashes": sorted(set(hashes)), "code": "\n".join(sources)}
            output.write(json.dumps(result) + "\n")
            output.flush()
            if index % 100 == 0 or index == len(pairs) + len(cards):
                print(f"campaign material {index}/{len(pairs) + len(cards)}", flush=True)


if __name__ == "__main__":
    main()
