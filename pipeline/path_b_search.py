"""Cache the fixed registry searches used for hard-negative path B.

    python pipeline/path_b_search.py --cache DIR --out FILE
"""
import argparse
import hashlib
import json
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

from collect import HN_CATEGORIES
from registry_fetch import request
from wyss import write_jsonl


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    cache = Path(args.cache)
    cache.mkdir(parents=True, exist_ok=True)
    rows = []
    for category, spec in HN_CATEGORIES.items():
        found = {}
        for keyword in spec["keywords"]:
            query = urllib.parse.urlencode({"text": keyword, "size": 250})
            url = f"https://registry.npmjs.org/-/v1/search?{query}"
            target = cache / (hashlib.sha256(keyword.encode()).hexdigest() + ".json")
            if not target.exists():
                target.write_bytes(request(url))
            for entry in json.loads(target.read_text())["objects"]:
                name = entry["package"]["name"]
                row = found.setdefault(name, {"name": name, "search_category": category,
                                              "keywords": [], "metadata_files": [],
                                              "status": "package_candidate_not_verified"})
                row["keywords"].append(keyword)
                row["metadata_files"].append(str(target))
        ordered = sorted(found.values(), key=lambda r: hashlib.sha256(r["name"].encode()).hexdigest())
        # Preserve the full search union for audit; inspection is bounded by D60.
        for rank, row in enumerate(ordered, 1):
            rows.append(dict(row, inspection_rank=rank, within_250_limit=rank <= 250))
        print(json.dumps({"category": category, "unique_packages": len(found),
                          "inspection_limit": min(250, len(found))}), flush=True)
    write_jsonl(args.out, rows)


if __name__ == "__main__":
    main()
