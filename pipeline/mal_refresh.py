"""Acquire a new pinned Datadog compromised-update inventory.

    python pipeline/mal_refresh.py --upstream DIR --out DIR
"""
import argparse
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import datadog_fetch
from registry_fetch import request
from wyss import write_jsonl

API = "https://api.github.com/repos/DataDog/malicious-software-packages-dataset"
RAW = "https://raw.githubusercontent.com/DataDog/malicious-software-packages-dataset"


def cached_json(path, url):
    if not path.exists():
        payload = request(url)
        json.loads(payload)
        path.write_bytes(payload)
    return json.loads(path.read_bytes())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--upstream", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    old_root = datadog_fetch.ROOT
    if args.upstream.resolve() == old_root.resolve():
        raise ValueError("the historical source must remain unchanged")
    historical = {row["id"] for row in datadog_fetch.candidates("compromised_lib")}
    args.upstream.mkdir(parents=True, exist_ok=True)
    args.out.mkdir(parents=True, exist_ok=True)
    commit = cached_json(args.upstream / "commit.json", API + "/commits/main")
    revision = commit["sha"]
    cached_json(args.upstream / "manifest-pinned.json", RAW + f"/{revision}/samples/npm/manifest.json")
    children = cached_json(args.upstream / "npm-tree.json", API + f"/contents/samples/npm?ref={revision}")
    tree_sha = next(row["sha"] for row in children if row["name"] == "compromised_lib")
    cached_json(args.upstream / "compromised-tree.json", API + f"/git/trees/{tree_sha}?recursive=1")
    datadog_fetch.ROOT = args.upstream
    pool = datadog_fetch.candidates("compromised_lib")
    new = [row for row in pool if row["id"] not in historical]
    write_jsonl(args.out / "pool.jsonl", pool)
    write_jsonl(args.out / "new-versions.jsonl", new)
    print(json.dumps({"revision": revision, "historical_versions": len(historical),
                      "current_versions": len(pool), "new_versions": len(new)}), flush=True)
    errors = 0
    with ThreadPoolExecutor(max_workers=4) as workers, (args.out / "archives.jsonl").open("w") as output:
        for index, row in enumerate(workers.map(lambda entry: datadog_fetch.fetch(entry, revision), new), 1):
            output.write(json.dumps(row) + "\n")
            output.flush()
            errors += bool(row.get("error"))
            print(json.dumps({"completed": index, "total": len(new), "errors": errors}), flush=True)
    pins = [{"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
            for path in sorted(args.upstream.glob("*.json"))]
    write_jsonl(args.out / "source-pins.jsonl", pins)
    summary = {"revision": revision, "historical_versions": len(historical),
               "current_versions": len(pool), "new_versions": len(new),
               "downloaded": len(new) - errors, "errors": errors,
               "screened_independent_pairs": None,
               "note": "New relative to historical Datadog inventory only; exposure screening pending."}
    (args.out / "download-summary.json").write_text(json.dumps(summary, indent=2) + "\n")


if __name__ == "__main__":
    main()
