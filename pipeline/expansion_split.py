"""Propose dev/test partitions for TYP/HN review candidates from combined campaigns.

    python pipeline/expansion_split.py --review TYP.jsonl HN.jsonl --campaigns D96.json \
        --sensitivity PRE_D96.json --exposure exposure-registry.jsonl --out DIR
"""
import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from samples import load_jsonl
from wyss import write_jsonl

EXPOSURE_FLAGS = ("pair_exposed", "package_exposed", "related_dependency_exposed")


def merge_review(paths):
    rows = {}
    for path in paths:
        for row in load_jsonl(path):
            entry = rows.setdefault(row["id"], dict(row, subsets=[]))
            entry["subsets"].append(row["subset"])
            for flag in EXPOSURE_FLAGS:
                entry[flag] = entry.get(flag, False) or row.get(flag, False)
    return rows


# exposed_members treats every MAL candidate as dev: all of them were evaluated.
def exposed_members(campaigns, roles, review, exposure):
    ids = {r["id"] for r in exposure}
    names = {r["name"] for r in exposure} | {n for r in exposure for n in r["related_names"]}
    exposed = set()
    for identity in campaigns:
        if identity in ids or roles.get(identity) == "mal_candidate":
            exposed.add(identity)
        elif identity in review and any(review[identity][f] for f in EXPOSURE_FLAGS):
            exposed.add(identity)
        elif identity.rsplit("@", 1)[0] in names:
            exposed.add(identity)
    return exposed


def assess(review, campaigns, roles, exposure):
    members = defaultdict(list)
    for identity, root in campaigns.items():
        members[root].append(identity)
    exposed = exposed_members(campaigns, roles, review, exposure)
    result = {}
    for identity, row in review.items():
        if identity not in campaigns:
            result[identity] = dict(campaign=None, reasons=["no_campaign_assignment"], eligible=False)
            continue
        root = campaigns[identity]
        reasons = [f for f in EXPOSURE_FLAGS if row[f]]
        if any(m in exposed for m in members[root] if m != identity):
            reasons.append("campaign_with_exposed_item")
        result[identity] = dict(
            campaign=root, campaign_size=len(members[root]),
            campaign_roles=dict(Counter(roles.get(m, "unknown") for m in members[root])),
            reasons=reasons, eligible=not reasons)
    return result


def partition(row, verdict):
    if not verdict["eligible"]:
        return "dev"
    # HN is split test/KB by gold category (methodology §3.3), which needs annotation first.
    return "hn-pending-annotation" if "HN" in row["subsets"] else "typ-test-candidate"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--review", nargs="+", required=True)
    parser.add_argument("--campaigns", required=True)
    parser.add_argument("--sensitivity", required=True)
    parser.add_argument("--exposure", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    review = merge_review(args.review)
    exposure = load_jsonl(args.exposure)
    primary = json.loads(Path(args.campaigns).read_text())
    sensitivity = json.loads(Path(args.sensitivity).read_text())
    roles = primary["item_roles"]
    for run in (primary, sensitivity):
        if not run["complete_for_available_items"]:
            raise SystemExit("campaign run has fingerprint failures; resolve them before splitting")
    main_verdicts = assess(review, primary["campaigns"], roles, exposure)
    pre_verdicts = assess(review, sensitivity["campaigns"], roles, exposure)

    rows = []
    for identity, row in sorted(review.items()):
        verdict, pre = main_verdicts[identity], pre_verdicts[identity]
        rows.append({
            "id": identity, "name": row["name"], "subsets": row["subsets"], "group": row.get("group"),
            "campaign": verdict["campaign"], "campaign_size": verdict.get("campaign_size"),
            "campaign_roles": verdict.get("campaign_roles"),
            "holdout_eligible": verdict["eligible"], "dev_reasons": verdict["reasons"],
            "proposed_partition": partition(row, verdict),
            "pre_d96_campaign": pre["campaign"], "pre_d96_holdout_eligible": pre["eligible"],
            "gold_label": None, "final": False,
        })
    out = Path(args.out)
    write_jsonl(out / "split-proposal.jsonl", rows)

    def count(key, subset=None):
        selected = [r for r in rows if subset is None or subset in r["subsets"]]
        return dict(Counter(str(r[key]) for r in selected))
    eligible_typ = [r for r in rows if r["proposed_partition"] == "typ-test-candidate"]
    eligible_hn = [r for r in rows if r["proposed_partition"] == "hn-pending-annotation"]
    summary = {
        "status": "proposal; not a frozen test set, no gold labels",
        "review_pairs": len(rows),
        "partition": count("proposed_partition"),
        "holdout_eligible_by_subset": {s: count("holdout_eligible", s) for s in ("TYP", "HN")},
        "pre_d96_holdout_eligible_by_subset": {s: count("pre_d96_holdout_eligible", s) for s in ("TYP", "HN")},
        "dev_reasons": dict(Counter(x for r in rows for x in r["dev_reasons"])),
        "typ_test_candidates_by_group": dict(Counter(r["group"] for r in eligible_typ)),
        "typ_test_candidate_campaigns": len({r["campaign"] for r in eligible_typ}),
        "hn_pending_campaigns": len({r["campaign"] for r in eligible_hn}),
        "eligible_sharing_campaign_with_kb": sum(
            bool((r["campaign_roles"] or {}).get("kb_pool")) for r in eligible_typ + eligible_hn),
        "largest_eligible_campaigns": Counter(
            r["campaign"] for r in eligible_typ + eligible_hn).most_common(10),
        "campaign_clusters": {"d96": primary["clusters"], "pre_d96": sensitivity["clusters"]},
    }
    (out / "split-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
