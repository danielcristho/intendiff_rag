"""Extend the D99 campaign closure with new source-labelled pairs offline.

    python pipeline/mal_expansion_campaign.py --pairs FILE --advisories FILE --out DIR
"""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from campaign_extend import extend
from campaign_fingerprints import similarity
from campaign_materials import material
from samples import load_jsonl
from wyss import write_jsonl

HISTORY = Path("data/preparation/source-labelled-20261014/campaigns-with-reports")
AUDIT = Path("data/acquisition/campaign-audit-20261013")
CACHE = Path("data/work/audit/fingerprints")


def proposals_for(pairs, campaigns, assigned, exposure):
    blocked_campaigns = {campaigns[identity] for identity in assigned}
    old_names = {identity.rsplit("@", 1)[0] for identity in assigned}
    exposed_names = set()
    for row in exposure:
        if row.get("name"):
            exposed_names.add(row["name"])
        exposed_names.update(row.get("related_names", []))
        if row.get("id") in campaigns:
            blocked_campaigns.add(campaigns[row["id"]])
    proposals, counts = [], {}
    for pair in sorted(pairs, key=lambda r: hashlib.sha256(r["id"].encode()).hexdigest()):
        reasons = []
        campaign = campaigns[pair["id"]]
        if pair["name"] in old_names:
            reasons.append("name_in_historical_pool")
        if pair["name"] in exposed_names:
            reasons.append("name_or_dependency_previously_exposed")
        if campaign in blocked_campaigns:
            reasons.append("campaign_in_historical_pool")
        if not reasons and counts.get(campaign, 0) >= 3:
            reasons.append("mal_campaign_cap")
        if not reasons:
            counts[campaign] = counts.get(campaign, 0) + 1
        proposals.append(dict(pair, campaign=campaign,
                              status="excluded" if reasons else "candidate_new_holdout",
                              exclusion_reasons=reasons,
                              pending_checks=["preprocessing_and_release_audit"] if not reasons else []))
    return proposals


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pairs", type=Path, required=True)
    parser.add_argument("--advisories", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    pins = {}

    def pinned(path):
        raw = path.read_bytes()
        pins[str(path)] = hashlib.sha256(raw).hexdigest()
        return raw

    for row in load_jsonl(HISTORY / "input-pins.jsonl"):
        if hashlib.sha256(Path(row["path"]).read_bytes()).hexdigest() != row["sha256"]:
            raise ValueError("historical campaign input changed: " + row["path"])
    old = []
    for path in (AUDIT / "material-index.jsonl", HISTORY / "added-materials.jsonl"):
        old.extend(json.loads(line) for line in pinned(path).splitlines() if line.strip())
    assigned = json.loads(pinned(HISTORY / "combined.json"))["campaigns"]
    if set(assigned) != {row["id"] for row in old}:
        raise ValueError("D99 campaign closure differs from inherited materials")
    pairs = [json.loads(line) for line in pinned(args.pairs).splitlines() if line.strip()]
    checks = {(r["name"], r["version"]): r for r in
              (json.loads(line) for line in pinned(args.advisories).splitlines() if line.strip())}
    added, fingerprints = [], {}
    for pair in pairs:
        check = checks[(pair["name"], pair["after"])]
        if check.get("error") or "advisory_ids" not in check:
            raise ValueError("missing target advisory check")
        reports = [key for key in check["advisory_ids"] if key.startswith("MAL-")]
        row = material(pair["id"], "external_mal_candidate", Path(pair["before_dir"]),
                       Path(pair["after_dir"]), reports)
        code = row.pop("code")
        key = hashlib.sha256(code.encode()).hexdigest()
        request = args.out / "fingerprint-request.json"
        request.write_text(json.dumps(dict(code=code)))
        result = subprocess.run(["dolos-fingerprints", str(request)], capture_output=True,
                                text=True, check=True, timeout=180)
        fingerprint = json.loads(result.stdout)
        if sum(fingerprint["counts"].values()) != fingerprint["total"]:
            raise ValueError("invalid new fingerprint")
        fingerprints[key] = fingerprint
        (args.out / (key + ".json")).write_text(json.dumps(fingerprint) + "\n")
        added.append(dict(row, code_key=key))
    scores = {}
    for index, key in enumerate(sorted({row["code_key"] for row in old}), 1):
        path = CACHE / (key + ".json")
        if not path.exists():
            path = HISTORY / (key + ".json")
        fingerprint = json.loads(pinned(path))
        for new_key, new in fingerprints.items():
            scores[new_key, key] = similarity(new, fingerprint)
        if index % 1000 == 0:
            print(json.dumps(dict(inherited_fingerprints_checked=index)), flush=True)

    def lookup(left, right):
        if (left, right) in scores:
            return scores[left, right]
        return similarity(fingerprints[left], fingerprints[right])

    campaigns, edges = extend(old, added, assigned, lookup)
    exposure = []
    frozen = Path("data/evaluation/source-rag-v3-20261015")
    for path in [Path("data/acquisition/expansion-full-20261013/exposure-registry.jsonl"),
                 *[frozen / name for name in ("test.pairs.jsonl", "dev.pairs.jsonl", "kb.jsonl")]]:
        exposure.extend(json.loads(line) for line in pinned(path).splitlines() if line.strip())
    proposals = proposals_for(pairs, campaigns, assigned, exposure)
    write_jsonl(args.out / "added-materials.jsonl", added)
    write_jsonl(args.out / "new-links.jsonl", edges)
    write_jsonl(args.out / "split-proposal.jsonl", proposals)
    write_jsonl(args.out / "input-pins.jsonl", [dict(path=p, sha256=d) for p, d in sorted(pins.items())])
    report = dict(campaigns=campaigns, items=len(campaigns), added=len(added), threshold=0.5,
                  clusters=len(set(campaigns.values())), inherited_old_closure=str(HISTORY / "combined.json"),
                  all_new_comparisons_checked=True, old_old_comparisons_rerun=False)
    (args.out / "combined.json").write_text(json.dumps(report, indent=2) + "\n")
    ready = [r for r in proposals if not r["exclusion_reasons"]]
    summary = dict(screened_pairs=len(pairs), inherited_items=len(assigned),
                   candidate_holdout_pairs=len(ready), candidate_holdout_campaigns=len({r["campaign"] for r in ready}),
                   excluded=len(pairs)-len(ready), test_released=False, inferences=0)
    (args.out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary), flush=True)


if __name__ == "__main__":
    main()
