"""Resolve compromised-version predecessors from archived registry metadata.

    python pipeline/datadog_pairs.py --inventory FILE --out-dir DIR
"""
import argparse
import json
from pathlib import Path

from collect import previous_version
from samples import load_jsonl
from wyss import write_jsonl


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory", required=True)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()
    out = Path(args.out_dir)
    manifest = json.loads(Path("data/upstream/datadog/manifest-pinned.json").read_text())
    candidates, excluded, wanted = [], [], {}
    for row in load_jsonl(args.inventory):
        if row["kind"] != "compromised_lib":
            continue
        try:
            if row.get("error"):
                raise ValueError(row["error"])
            documents = [json.loads(Path(p).read_text()) for p in row["package_info"]]
            documents = [d for d in documents if d.get("name") == row["name"]
                         and isinstance(d.get("versions"), dict)]
            if len(documents) != 1:
                raise ValueError("no unique archived packument for this package")
            document = documents[0]
            before = previous_version(document, row["version"])
            if before is None:
                raise ValueError("no predecessor with verified publication order")
            if before in (manifest[row["name"]] or []):
                raise ValueError("immediate semver predecessor is also listed compromised")
            candidates.append({"id": row["id"], "name": row["name"], "before": before,
                               "after": row["version"], "published_at": document["time"][row["version"]],
                               "published_before": document["time"][before], "after_dir": row["dir"],
                               "source": "datadog", "source_url": row["source_url"],
                               "source_revision": row["revision"], "source_label": "malicious",
                               "source_archive_sha256": row["sha256"],
                               "annotation_status": "pending", "package_info": row["package_info"]})
            wanted[(row["name"], before)] = {"name": row["name"], "version": before, "origin": "registry"}
        except Exception as exc:
            excluded.append({"id": row["id"], "name": row["name"], "version": row["version"],
                             "reason": str(exc)})
    write_jsonl(out / "datadog.pair-candidates.jsonl", candidates)
    write_jsonl(out / "datadog.pair-exclusions.jsonl", excluded)
    write_jsonl(out / "wanted.datadog-before.jsonl", wanted.values())
    print(json.dumps({"pair_candidates": len(candidates), "excluded": len(excluded),
                      "unique_predecessors": len(wanted)}))


if __name__ == "__main__":
    main()
