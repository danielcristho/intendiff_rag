"""Acquire pinned Datadog archives without opening or executing samples.

    python pipeline/datadog_fetch.py --kind compromised_lib --out FILE
"""
import argparse
import hashlib
import json
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from registry_fetch import request
from wyss import write_jsonl

ROOT = Path("data/upstream/datadog")


def candidates(kind):
    manifest = json.loads((ROOT / "manifest-pinned.json").read_text())
    names = {name.replace("/", "@"): name for name in manifest}
    tree = "compromised-tree.json" if kind == "compromised_lib" else "intent-tree.json"
    document = json.loads((ROOT / tree).read_text())
    if document.get("truncated"):
        raise ValueError("truncated source tree cannot define the candidate pool")
    rows = []
    for entry in document["tree"]:
        if not entry["path"].endswith(".zip"):
            continue
        folder, version, filename = entry["path"].split("/")
        name = names.get(folder)
        if name is None:
            raise ValueError(f"archive package is absent from manifest: {folder}")
        source_label = manifest[name]
        if kind == "compromised_lib" and (not isinstance(source_label, list) or version not in source_label):
            continue
        if kind == "malicious_intent" and source_label is not None:
            continue
        rows.append({"id": f"{name}@{version}", "name": name, "version": version,
                     "kind": kind, "path": f"samples/npm/{kind}/{entry['path']}",
                     "git_blob_sha1": entry["sha"], "bytes": entry["size"]})
    # Multiple discovery dates can refer to the same version; retain the first path.
    unique = {}
    for row in sorted(rows, key=lambda r: r["path"]):
        unique.setdefault(row["id"], row)
    return sorted(unique.values(), key=lambda r: hashlib.sha256(r["id"].encode()).hexdigest())


def fetch(row, revision):
    target = ROOT / "archives" / row["kind"] / (hashlib.sha256(row["id"].encode()).hexdigest() + ".zip")
    target.parent.mkdir(parents=True, exist_ok=True)
    url = "https://raw.githubusercontent.com/DataDog/malicious-software-packages-dataset/" + revision + "/" + urllib.parse.quote(row["path"], safe="/@")
    try:
        payload = target.read_bytes() if target.exists() else request(url)
        git_digest = hashlib.sha1(f"blob {len(payload)}\0".encode() + payload).hexdigest()
        if git_digest != row["git_blob_sha1"]:
            raise ValueError("archive differs from pinned Git blob")
        if not target.exists():
            target.write_bytes(payload)
        return dict(row, archive=str(target), sha256=hashlib.sha256(payload).hexdigest(),
                    revision=revision, source_url=url)
    except Exception as exc:
        return dict(row, error=str(exc), source_url=url)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", required=True, choices=("compromised_lib", "malicious_intent"))
    parser.add_argument("--out", required=True)
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    pool = candidates(args.kind)
    write_jsonl(Path(args.out).with_suffix(".pool.jsonl"), pool)
    wanted = pool[:args.limit]
    revision = json.loads((ROOT / "commit.json").read_text())["sha"]
    with ThreadPoolExecutor(max_workers=6) as workers, Path(args.out).open("w") as output:
        for index, row in enumerate(workers.map(lambda r: fetch(r, revision), wanted), 1):
            output.write(json.dumps(row) + "\n")
            output.flush()
            if row.get("error"):
                print(json.dumps(row), flush=True)
            if index % 50 == 0 or index == len(wanted):
                print(f"downloaded {index}/{len(wanted)} ({len(pool)} eligible archive versions)", flush=True)
