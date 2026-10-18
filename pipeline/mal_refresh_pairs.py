"""Resolve newly acquired compromised versions against source metadata.

    python pipeline/mal_refresh_pairs.py --root DIR --upstream DIR
"""
import argparse
import hashlib
import json
from pathlib import Path

from collect import previous_version
from external_mal import guo_versions
from samples import load_jsonl
from wyss import write_jsonl


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--upstream", type=Path, required=True)
    args = parser.parse_args()
    manifest_path = args.upstream / "manifest-pinned.json"
    manifest = json.loads(manifest_path.read_text())
    roles = json.loads(Path("data/acquisition/campaigns-20261013/combined-d96.json").read_text())["item_roles"]
    malicious = {identity for identity, role in roles.items() if role in ("mal_candidate", "kb_pool")}
    malicious.update(row["id"] for row in guo_versions())
    candidates, excluded, wanted = [], [], []
    for row in load_jsonl(args.root / "inventory.jsonl"):
        try:
            if row.get("error") or row.get("rejected"):
                raise ValueError("target archive invalid or has rejected entries")
            versions = manifest.get(row["name"])
            if not isinstance(versions, list) or row["version"] not in versions:
                raise ValueError("target is not a source-labelled compromised version")
            documents = [(Path(p), json.loads(Path(p).read_text())) for p in row["package_info"]]
            documents = [(p, d) for p, d in documents if d.get("name") == row["name"]
                         and isinstance(d.get("versions"), dict)]
            if len(documents) != 1:
                raise ValueError("no unique archived registry metadata")
            metadata_path, document = documents[0]
            before = previous_version(document, row["version"])
            if before is None:
                raise ValueError("no predecessor with verified publication order")
            if before in versions or f"{row['name']}@{before}" in malicious:
                raise ValueError("predecessor listed malicious by a held source")
            candidates.append(dict(
                id=row["id"], name=row["name"], before=before, after=row["version"],
                after_dir=row["dir"], published_at=document["time"][row["version"]],
                published_before=document["time"][before], subset="MAL",
                source="datadog", source_label="malicious", annotation_status="source_labelled",
                source_url=row["source_url"], source_revision=row["revision"],
                source_archive_sha256=row["sha256"], source_manifest=str(manifest_path),
                source_manifest_sha256=hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
                metadata_file=str(metadata_path),
                metadata_sha256=hashlib.sha256(metadata_path.read_bytes()).hexdigest(),
                pending_checks=["predecessor_archive", "advisory", "campaign_and_exposure"]))
            wanted.append(dict(name=row["name"], version=before, origin="registry"))
        except (ValueError, KeyError, OSError) as exc:
            excluded.append(dict(id=row["id"], reason=str(exc)))
    write_jsonl(args.root / "pair-candidates.jsonl", candidates)
    write_jsonl(args.root / "pair-exclusions.jsonl", excluded)
    write_jsonl(args.root / "wanted.before.jsonl", wanted)
    print(json.dumps({"candidate_pairs": len(candidates), "excluded": len(excluded)}))


if __name__ == "__main__":
    main()
