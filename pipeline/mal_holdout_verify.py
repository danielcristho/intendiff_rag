"""Audit the combined D103/D104 candidate holdout before preprocessing.

    python pipeline/mal_holdout_verify.py --root DIR
"""
import argparse
import hashlib
import json
from pathlib import Path

from registry_fetch import integrity_ok
from mal_leads import source_rows
from samples import load_jsonl
from source_acquisition_verify import digest, tree_digest
from wyss import write_jsonl


def audit(root):
    draz = root / "draz"
    previous = Path("data/acquisition/mal-expansion-20261016")
    campaigns = root / "campaigns-with-exposure"
    archives = {(r["name"], r["version"]): r for r in load_jsonl(draz / "archives.jsonl")}
    records = {r["id"]: r for r in load_jsonl(draz / "advisory-record-pins.jsonl")}
    inherited = {r["id"]: r for r in load_jsonl(previous / "pairs.manifest.jsonl")}
    artifact = Path("data/upstream/draz-20261016/artifact.zip")
    record = json.loads(Path("data/upstream/draz-20261016/record.json").read_text())["files"][0]
    raw = artifact.read_bytes()
    algorithm, expected = record["checksum"].split(":", 1)
    if len(raw) != record["size"] or hashlib.new(algorithm, raw).hexdigest() != expected:
        raise ValueError("Draz artifact differs from the Zenodo checksum")
    leads, member, member_hash = source_rows(artifact)
    lead_records = {json.dumps(r, sort_keys=True) for r in leads}
    pins = {}
    for path in [*draz.glob("*.jsonl"), root / "combined-candidates.jsonl",
                 root / "combined-advisories.after.jsonl", campaigns / "split-proposal.jsonl",
                 campaigns / "combined.json", Path("data/upstream/draz-20261016/artifact.zip"),
                 Path("data/upstream/draz-20261016/record.json")]:
        pins[str(path)] = digest(path)
    for report in (previous / "acquisition-verification.json", previous / "preparation-verification.json"):
        for pin in json.loads(report.read_text())["input_pins"]:
            if digest(pin["path"]) != pin["sha256"]:
                raise ValueError("historical D103 input changed: " + pin["path"])
    for pin in load_jsonl(campaigns / "input-pins.jsonl") + list(records.values()):
        if pin.get("error") or digest(pin["path"]) != pin["sha256"]:
            raise ValueError("campaign or advisory pin changed")
        pins[pin["path"]] = pin["sha256"]
    accepted = []
    for proposal in load_jsonl(campaigns / "split-proposal.jsonl"):
        if proposal["status"] != "candidate_new_holdout":
            continue
        pair = dict(proposal)
        if pair["id"] in inherited:
            pair.update(inherited[pair["id"]])
            pair["campaign"] = proposal["campaign"]
        else:
            if (pair["source_member"] != member or pair["source_member_sha256"] != member_hash
                    or json.dumps(pair["lead_record"], sort_keys=True) not in lead_records):
                raise ValueError("lead differs from the original Draz artifact")
            if digest(pair["metadata_file"]) != pair["metadata_sha256"]:
                raise ValueError("registry metadata changed")
            document = json.loads(Path(pair["metadata_file"]).read_text())
            pins[pair["metadata_file"]] = pair["metadata_sha256"]
            if not pair["published_before"] < pair["published_at"]:
                raise ValueError("publication order mismatch")
            for side in ("before", "after"):
                archive = archives[pair["name"], pair[side]]
                if digest(archive["tarball"]) != pair["sha256_" + side]:
                    raise ValueError("archive changed")
                raw = Path(archive["tarball"]).read_bytes()
                if not integrity_ok(raw, document["versions"][pair[side]]["dist"]):
                    raise ValueError("registry integrity mismatch")
                pins[archive["tarball"]] = pair["sha256_" + side]
            for identity in pair["advisory_after"]["advisory_ids"]:
                if not identity.startswith("MAL-"):
                    continue
                report = json.loads(Path(records[identity]["path"]).read_text())
                if report.get("withdrawn"):
                    raise ValueError("MAL advisory was withdrawn")
                if not any(r.get("package", {}).get("name") == pair["name"]
                           and r["package"].get("ecosystem") == "npm" for r in report["affected"]):
                    raise ValueError("MAL advisory package mismatch")
        for side in ("before", "after"):
            if tree_digest(pair[side + "_dir"]) != pair["sha256_" + side + "_tree"]:
                raise ValueError("extracted source tree changed")
            package = json.loads((Path(pair[side + "_dir"]) / "package.json").read_text())
            if (package.get("name"), package.get("version")) != (pair["name"], pair[side]):
                raise ValueError("package identity mismatch")
        pair.update(evaluation_scope="candidate_new_holdout", label="malicious",
                    annotation_status="source_labelled", pending_checks=["preprocessing_and_release_audit"])
        accepted.append(pair)
    write_jsonl(root / "pairs.manifest.jsonl", accepted)
    report = dict(verified=True, candidate_pairs=len(accepted),
                  candidate_campaigns=len({r["campaign"] for r in accepted}),
                  previous_batch_pairs=sum(r["id"] in inherited for r in accepted),
                  new_batch_pairs=sum(r["id"] not in inherited for r in accepted),
                  test_released=False, inferences=0, sample_execution=False,
                  input_pins=[dict(path=p, sha256=h) for p, h in sorted(pins.items())])
    (root / "acquisition-verification.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "input_pins"}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    audit(parser.parse_args().root)
