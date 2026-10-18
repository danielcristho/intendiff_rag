"""Verify prepared MAL candidates and report their distinct campaign coverage.

    python pipeline/mal_preparation_verify.py --root DIR
"""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from samples import load_jsonl
from source_acquisition_verify import digest, tree_digest
from wyss import write_jsonl


def verify(root):
    acquired = json.loads((root / "acquisition-verification.json").read_text())
    for pin in acquired["input_pins"]:
        if digest(pin["path"]) != pin["sha256"]:
            raise ValueError("acquisition input changed: " + pin["path"])
    manifest = {r["id"]: r for r in load_jsonl(root / "pairs.manifest.jsonl")}
    attempts = load_jsonl(root / "pairs.preprocessed.jsonl")
    latest = {r["id"]: r for r in attempts}
    if set(latest) != set(manifest) or any(r.get("error") for r in latest.values()):
        raise ValueError("preprocessing incomplete or contains unresolved failures")
    for identity, row in latest.items():
        pair = manifest[identity]
        for key in ("name", "before", "after", "campaign", "label", "source_label", "label_provenance"):
            if row.get(key) != pair.get(key):
                raise ValueError("prepared metadata mismatch: " + key)
        if row["intent_from"] != pair["before"] or row["preprocessing"]["version"] != "static-dolos-exact-v2":
            raise ValueError("intent source or normalization version mismatch")
        if hashlib.sha256(row["diff"].encode()).hexdigest() != row["diff_sha256"]:
            raise ValueError("diff digest mismatch")
        for side in ("before", "after"):
            if row["sha256_" + side] != pair["sha256_" + side]:
                raise ValueError("prepared archive hash mismatch")
            if tree_digest(pair[side + "_dir"]) != pair["sha256_" + side + "_tree"]:
                raise ValueError("source tree changed during preprocessing")
    prepared = [latest[key] for key in sorted(manifest)]
    write_jsonl(root / "pairs.prepared.jsonl", prepared)
    campaigns = json.loads((root / "campaigns-with-exposure/combined.json").read_text())["campaigns"]
    old = [r for r in load_jsonl("data/evaluation/source-rag-v3-20261015/test.pairs.jsonl") if r["label"] == "malicious"]
    old_groups = {campaigns[r["id"]] for r in old}
    new_groups = {campaigns[r["id"]] for r in prepared}
    if old_groups & new_groups:
        raise ValueError("new candidates overlap historical test campaigns")
    files = [root / name for name in ("pairs.manifest.jsonl", "pairs.preprocessed.jsonl", "pairs.prepared.jsonl",
                                      "acquisition-verification.json", "campaigns-with-exposure/combined.json")]
    files += [Path("pipeline") / name for name in ("mal_leads.py", "mal_lead_archives.py", "mal_holdout_verify.py",
              "mal_preparation_verify.py", "mal_expansion_campaign.py", "preprocess_corpus.py", "dataset.py",
              "normalization.py", "smartdiff.py", "intent.py", "capability.py")]
    summary = dict(verified=True, prepared_candidate_pairs=len(prepared), candidate_campaigns=len(new_groups),
                   previous_batch_pairs=acquired["previous_batch_pairs"], new_batch_pairs=acquired["new_batch_pairs"],
                   historical_test_mal_pairs=len(old), historical_test_campaigns=len(old_groups),
                   combined_mal_pairs=len(old)+len(prepared), combined_campaigns=len(old_groups | new_groups),
                   publication_years=dict(Counter(r["published_at"][:4] for r in prepared)),
                   preprocessing_failures=sum(bool(r.get("error")) for r in attempts),
                   raw_fallback_files=sum(r["preprocessing"].get("fallback_files", 0) for r in prepared),
                   truncated_diffs=sum(bool(r["truncated"]) for r in prepared),
                   source_trees_unchanged=True, human_labels_created=0, inferences=0, test_released=False,
                   pending_checks=["separate_evaluation_protocol_and_per_model_context_audit"],
                   input_pins=[dict(path=str(p), sha256=digest(p)) for p in files])
    (root / "preparation-verification.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({k: v for k, v in summary.items() if k != "input_pins"}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    verify(parser.parse_args().root)
