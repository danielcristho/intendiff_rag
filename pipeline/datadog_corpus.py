"""Extract and inventory Datadog samples in a network-disabled container.

    python pipeline/datadog_corpus.py --manifest FILE --into DIR --out FILE
"""
import argparse
import hashlib
import json
from concurrent.futures import ProcessPoolExecutor
from functools import partial
from pathlib import Path

import archives
import capability
from samples import load_jsonl


def inventory(row, into):
    if row.get("error"):
        return row
    key = hashlib.sha256(row["id"].encode()).hexdigest()
    destination = Path(into) / key
    try:
        archive = Path(row["archive"])
        with archive.open("rb") as stream:
            if hashlib.file_digest(stream, "sha256").hexdigest() != row["sha256"]:
                raise ValueError("archive changed after download")
        extraction = archives.extract(archive, destination, password=b"infected")
        manifests = []
        for path in destination.rglob("package.json"):
            candidate = capability.package_json(path.parent)
            if candidate.get("name") == row["name"] and str(candidate.get("version", "")).split("+", 1)[0] == row["version"].split("+", 1)[0]:
                manifests.append(path.parent)
        if len(manifests) != 1:
            raise ValueError(f"expected one matching package.json, found {len(manifests)}")
        package = manifests[0]
        # This scans source text only; npm scripts and imported code never run.
        signals = capability.capabilities(package)
        metadata = list(destination.rglob("package_info-*.json"))
        return dict(row, dir=str(package), capabilities=signals,
                    package_info=[str(p) for p in metadata],
                    extracted_files=extraction["files"], rejected=extraction["rejected"],
                    annotation_status="pending")
    except Exception as exc:
        return dict(row, error=str(exc))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--into", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    rows = load_jsonl(args.manifest)
    completed = {r["id"] for r in load_jsonl(args.out) if not r.get("error")}
    completed.intersection_update(r["id"] for r in rows)
    pending = [r for r in rows if r["id"] not in completed]
    with ProcessPoolExecutor(max_workers=4) as workers, Path(args.out).open("a") as output:
        for index, row in enumerate(workers.map(partial(inventory, into=args.into), pending), 1):
            output.write(json.dumps(row) + "\n")
            output.flush()
            if row.get("error"):
                print(json.dumps({"id": row["id"], "error": row["error"]}), flush=True)
            if index % 50 == 0 or index == len(pending):
                print(f"inventoried {len(completed) + index}/{len(rows)}", flush=True)
