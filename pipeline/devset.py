"""Assemble the dev set (§3.5): Wyss malicious clones plus unused TYP draws.

    python pipeline/devset.py --out data/pairs.dev.jsonl
    python pipeline/devset.py --selfcheck
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import intent  # noqa: E402
from capability import package_root  # noqa: E402
from collect import draw_typical, hash_key, listing_entry, read_listing  # noqa: E402
from pairs import assign_campaigns, build_row  # noqa: E402

CLONES = 4
TYPICAL = 3


# read_clones parses malicious_clones.txt, whose after side is a bare directory.
def read_clones(path):
    entries = []
    for line in Path(path).read_text().splitlines():
        if not line.strip():
            continue
        before_path, after_path = line.strip().split(",")
        name, before = listing_entry(before_path)
        # "j_samples/agent-base/agentbas-7.1.1" carries no "@": the clone
        # directory is its only identity, so it stands in for the version.
        entries.append({"name": name, "before": before, "after": after_path.rsplit("/", 1)[1],
                        "before_path": before_path, "after_path": after_path})
    return entries


# draw_clones takes the first clones in hash order.
def draw_clones(entries, take=CLONES):
    return sorted(entries, key=lambda entry: hash_key(entry["name"], entry["after"]))[:take]


# unused_typical drops every pair already drawn into the TYP test subset.
def unused_typical(listings, typ_pairs):
    taken = {json.loads(line)["id"] for line in Path(typ_pairs).read_text().splitlines() if line}
    return [entry for listing in listings for entry in read_listing(listing)
            if f"{entry['name']}@{entry['after']}" not in taken]


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--wyss", default="data/wyss")
    parser.add_argument("--typ-pairs", default="data/pairs.typ.jsonl")
    parser.add_argument("--typ-out", default="data/typ")
    parser.add_argument("--out", default="data/pairs.dev.jsonl")
    args = parser.parse_args(argv)

    wyss = Path(args.wyss)
    clones = draw_clones(read_clones(wyss / "data/malicious_clones.txt"))
    listings = [wyss / "data/typical_updates_popular.txt", wyss / "data/typical_updates_random.txt"]
    typical, rejected = draw_typical(unused_typical(listings, args.typ_pairs), TYPICAL, args.typ_out)
    for pair_id, why in rejected:
        print(f"  ditolak {pair_id}: {why}")

    count = intent.qwen_counter()
    rows, sides = [], []
    for entries, root, subset, source in ((clones, wyss / "samples", "MAL", "wyss-osf-clone"),
                                          (typical, Path(args.typ_out), "TYP", "wyss-typical")):
        for entry in entries:
            before, after = (package_root(root / entry[side]) for side in ("before_path", "after_path"))
            rows.append(build_row(entry["name"], entry["before"], entry["after"],
                                  before, after, subset, source, count))
            sides.append((before, after))
    assign_campaigns(rows, sides)

    out = Path(args.out)
    with out.open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")
    # Path A (§3.3) must skip these, or a dev pair could reappear as an HN test item.
    taken = out.with_suffix(".taken.txt")
    taken.write_text("".join(f"{entry['before_path']},{entry['after_path']}\n" for entry in typical))
    print(f"{out}: {len(rows)} pair ({len(clones)} clone, {len(typical)} TYP); {taken}")
    # TODO: 3 HN from the KB share (§3.5) once the HN split exists.


def selfcheck():
    import tempfile

    with tempfile.TemporaryDirectory() as work:
        listing = Path(work) / "clones.txt"
        listing.write_text(
            "j_samples/agent-base/agent-base@7.1.1,j_samples/agent-base/agentbas-7.1.1\n"
            "j_samples/@scope/x/@scope/x@1.0.0,j_samples/@scope/x/sc-x-1.0.0\n"
        )
        entries = read_clones(listing)
        # A clone keeps its original as the before side and its directory as the after side.
        assert entries[0]["name"] == "agent-base" and entries[0]["before"] == "7.1.1", entries
        assert entries[0]["after"] == "agentbas-7.1.1", entries
        assert entries[1]["name"] == "@scope/x" and entries[1]["after"] == "sc-x-1.0.0", entries
        # The draw depends on the hash, not on listing order.
        assert draw_clones(entries, 2) == draw_clones(entries[::-1], 2)

        typical = Path(work) / "typ.txt"
        typical.write_text("r/a/a@1.0.0,r/a/a@1.0.1\nr/b/b@2.0.0,r/b/b@2.1.0\n")
        typ_pairs = Path(work) / "pairs.typ.jsonl"
        typ_pairs.write_text(json.dumps({"id": "a@1.0.1"}) + "\n")
        # A pair already in the TYP test subset never enters the dev set.
        assert [entry["name"] for entry in unused_typical([typical], typ_pairs)] == ["b"]
    print("devset selfcheck ok")


if __name__ == "__main__":
    if "--selfcheck" in sys.argv:
        selfcheck()
    else:
        main()
