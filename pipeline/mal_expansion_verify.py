"""Verify acquired MAL candidates and write a preparation manifest offline.

    python pipeline/mal_expansion_verify.py --root DIR
"""
import argparse
import hashlib
import json
from pathlib import Path

from samples import load_jsonl
from source_acquisition_verify import digest, tree_digest
from wyss import write_jsonl


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    root = parser.parse_args().root
    acquisition = root / "datadog"
    campaigns = root / "campaigns-with-exposure"
    archive_rows = load_jsonl(acquisition / "archives.jsonl")
    targets = {r["id"]: r for r in archive_rows}
    predecessors = {(r["name"], r["version"]): r for r in load_jsonl(acquisition / "archives.before.jsonl")}
    checks = {(r["name"], r["version"]): r for r in load_jsonl(acquisition / "advisories.before.jsonl")}
    pins = {}
    for path in [*acquisition.glob("*.jsonl"), campaigns / "split-proposal.jsonl", campaigns / "combined.json"]:
        pins[str(path)] = digest(path)
    for row in load_jsonl(campaigns / "input-pins.jsonl") + load_jsonl(acquisition / "source-pins.jsonl"):
        if digest(row["path"]) != row["sha256"]:
            raise ValueError("pinned input changed: " + row["path"])
        pins[row["path"]] = row["sha256"]
    for row in archive_rows:
        raw = Path(row["archive"]).read_bytes()
        if hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest() != row["git_blob_sha1"]:
            raise ValueError("target Git blob mismatch")
        if hashlib.sha256(raw).hexdigest() != row["sha256"]:
            raise ValueError("target archive changed")
        pins[row["archive"]] = row["sha256"]
    accepted = []
    for row in load_jsonl(campaigns / "split-proposal.jsonl"):
        if row["status"] != "candidate_new_holdout":
            continue
        manifest = json.loads(Path(row["source_manifest"]).read_text())
        if row["after"] not in manifest[row["name"]] or row["before"] in manifest[row["name"]]:
            raise ValueError("pair label disagrees with pinned source")
        if digest(row["source_manifest"]) != row["source_manifest_sha256"] or digest(row["metadata_file"]) != row["metadata_sha256"]:
            raise ValueError("pair source metadata changed")
        before = predecessors[row["name"], row["before"]]
        if not before["registry_integrity_verified"] or digest(before["tarball"]) != row["sha256_before_tarball"]:
            raise ValueError("predecessor archive changed")
        advisory = checks[row["name"], row["before"]]
        if advisory.get("error") or advisory.get("has_advisory") is not False:
            raise ValueError("predecessor advisory gate failed")
        for side in ("before", "after"):
            package = json.loads((Path(row[side + "_dir"]) / "package.json").read_text())
            if (package.get("name"), package.get("version")) != (row["name"], row[side]):
                raise ValueError("extracted package identity mismatch")
        before_tree, after_tree = tree_digest(row["before_dir"]), tree_digest(row["after_dir"])
        if before_tree != row["tree_sha256_before"]:
            raise ValueError("predecessor tree changed")
        pins[before["tarball"]] = before["sha256"]
        pins[row["metadata_file"]] = row["metadata_sha256"]
        accepted.append(dict(row, label="malicious", evaluation_scope="candidate_new_holdout",
                             sha256_before=before["sha256"], sha256_after=targets[row["id"]]["sha256"],
                             sha256_before_tree=before_tree, sha256_after_tree=after_tree,
                             label_provenance=dict(path=row["source_manifest"], sha256=row["source_manifest_sha256"],
                                                   record_id=row["id"], basis="source_malicious")))
    write_jsonl(root / "pairs.manifest.jsonl", accepted)
    report = dict(verified=True, candidate_pairs=len(accepted), campaigns=len({r["campaign"] for r in accepted}),
                  downloaded_target_archives_verified=len(archive_rows), test_released=False,
                  sample_execution=False, human_labels_created=0, inferences=0,
                  input_pins=[dict(path=p, sha256=h) for p, h in sorted(pins.items())])
    (root / "acquisition-verification.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "input_pins"}))


if __name__ == "__main__":
    main()
