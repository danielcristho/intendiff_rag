"""Cache Dolos fingerprints and cluster combined campaign candidates offline.

    python pipeline/campaign_fingerprints.py --items FILE --cache DIR --out FILE
"""
import argparse
import hashlib
import json
import subprocess
import tempfile
from collections import Counter
from functools import lru_cache
from pathlib import Path

import campaign


def similarity(left, right):
    if not left["total"] + right["total"]:
        return 0.0
    small, large = sorted((left["counts"], right["counts"]), key=len)
    covered = sum(count + large[key] for key, count in small.items() if key in large)
    return covered / (left["total"] + right["total"])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--items", required=True, nargs="+")
    parser.add_argument("--cache", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--hash-rule", choices=("d96", "pre-d96"), default="d96",
                        help="pre-d96 also links items through trivial files")
    parser.add_argument("--scope", default="available MAL plus downloaded KB prefix; not the final pool")
    args = parser.parse_args()
    total = 0
    for path in args.items:
        with Path(path).open() as source:
            total += sum(bool(line.strip()) for line in source)
    source = (line for path in args.items for line in Path(path).open())
    items = []
    cache = Path(args.cache)
    cache.mkdir(parents=True, exist_ok=True)
    fingerprints, failures = {}, []
    for index, line in enumerate(source, 1):
        row = json.loads(line)
        key = hashlib.sha256(row["code"].encode()).hexdigest()
        row["code_key"] = key
        trivial = row.pop("trivial_hashes", [])
        if args.hash_rule == "pre-d96":
            row["added_hashes"] = sorted(set(row["added_hashes"]) | set(trivial))
        target = cache / (key + ".json")
        try:
            if key not in fingerprints:
                if not target.exists():
                    with tempfile.TemporaryDirectory() as temporary:
                        request = Path(temporary) / "input.json"
                        request.write_text(json.dumps({"code": row["code"]}))
                        result = subprocess.run(["dolos-fingerprints", str(request)], capture_output=True,
                                                text=True, check=True, timeout=args.timeout)
                        parsed = json.loads(result.stdout)
                        assert sum(parsed["counts"].values()) == parsed["total"]
                        target.write_text(json.dumps(parsed))
                fingerprints[key] = json.loads(target.read_text())
        except Exception as exc:
            failures.append({"id": row["id"], "error": str(exc)[:500], "code_key": key})
        row.pop("code")
        items.append(row)
        if index % 10 == 0 or index == total:
            print(json.dumps({"fingerprinted": index, "total": total, "failures": len(failures)}), flush=True)
    successful = [row for row in items if row["code_key"] in fingerprints]
    for row in successful:
        row["code"] = row["code_key"]
    @lru_cache(maxsize=65536)
    def cached_score(left, right):
        return similarity(fingerprints[left], fingerprints[right])

    def lookup(left, right):
        return cached_score(*sorted((left, right)))
    assigned = {str(threshold): campaign.cluster(successful, lookup, threshold)
                for threshold in campaign.REPORTED_THRESHOLDS}
    result = {"scope": args.scope, "hash_rule": args.hash_rule,
              "complete_for_available_items": not failures, "items": len(items),
              "roles": dict(Counter(row["role"] for row in items)), "failures": failures,
              "campaigns": assigned["0.5"], "item_roles": {row["id"]: row["role"] for row in items},
              "clusters": {threshold: len(set(groups.values())) for threshold, groups in assigned.items()},
              "largest_campaigns": Counter(assigned["0.5"].values()).most_common(10)}
    Path(args.out).write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k not in ("campaigns", "item_roles")}), flush=True)


if __name__ == "__main__":
    main()
