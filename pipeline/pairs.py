"""Assemble data/pairs.jsonl from extracted version directories.

    python pipeline/pairs.py --listing data/wyss/data/malicious_updates.txt \
        --roots data/wyss/samples --subset MAL --source wyss-osf --out data/pairs.jsonl
    python pipeline/pairs.py --selfcheck
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import campaign  # noqa: E402
import capability  # noqa: E402
import intent  # noqa: E402
import smartdiff  # noqa: E402
from capability import has_content, package_root  # noqa: E402
from collect import read_listing  # noqa: E402


# tree_digest hashes a directory as sorted "path\0sha256" lines.
def tree_digest(root):
    root = Path(root)
    lines = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        lines.append(f"{path.relative_to(root).as_posix()}\0{digest}")
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


# build_row assembles one pairs.jsonl entry from a before and after directory.
def build_row(name, before_version, after_version, before, after, subset, source, count):
    profile = intent.build(before, count)
    diff = smartdiff.build(before, after, count)
    return {
        "id": f"{name}@{after_version}",
        "name": name,
        "before": before_version,
        "after": after_version,
        "subset": subset,
        "category": None,
        "campaign": None,  # filled once every row is known (§3.6)
        "source": source,
        # The replication package ships extracted trees, not tarballs, so the
        # checksum covers the tree instead. Same guarantee, different input (D59).
        "published_at": None,
        "sha256_before": tree_digest(before),
        "sha256_after": tree_digest(after),
        "intent": profile,
        "intent_available": intent.available(profile),
        "intent_from": before_version,
        "delta": capability.delta(before, after),
        "delta_evidence": capability.delta_evidence(before, after),
        "diff": diff["diff"],
        "truncated": diff["truncated"],
        "label": "malicious" if subset == "MAL" else "benign",
        "gold_evidence": [],  # §8 annotation, never derived from the extractor
    }


# assign_campaigns clusters the rows in place by §3.6 criteria (a) and (b).
def assign_campaigns(rows, sides):
    items = []
    for row, (before, after) in zip(rows, sides):
        items.append({
            "id": row["id"],
            "reports": [],  # advisory ids arrive with the HN and TYP passes
            "added_hashes": campaign.added_hashes(before, after),
            "code": "",
        })
    labels = campaign.cluster(items)
    for row in rows:
        row["campaign"] = labels[row["id"]]


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--listing", required=True)
    parser.add_argument("--roots", required=True, help="directory the listing paths sit under")
    parser.add_argument("--subset", required=True, choices=("MAL", "HN", "TYP"))
    parser.add_argument("--source", required=True)
    parser.add_argument("--out", default="data/pairs.jsonl")
    args = parser.parse_args(argv)

    roots = Path(args.roots)
    count = intent.qwen_counter()
    entries = read_listing(args.listing)

    rows, kept, skipped = [], [], []
    for entry in entries:
        sides = [package_root(roots / entry[side]) for side in ("before_path", "after_path")]
        if not all(side.is_dir() and has_content(side) for side in sides):
            # An empty side is not an update: diffing against it would present
            # the whole package as newly added.
            skipped.append(f"{entry['name']}@{entry['after']}")
            continue
        before_dir, after_dir = sides
        rows.append(build_row(entry["name"], entry["before"], entry["after"],
                              before_dir, after_dir, args.subset, args.source, count))
        kept.append(sides)

    assign_campaigns(rows, kept)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")

    campaigns = len({row["campaign"] for row in rows})
    truncated = sum(1 for row in rows if row["truncated"])
    without_intent = sum(1 for row in rows if not row["intent_available"])
    print(f"{out}: {len(rows)} pair, {campaigns} kampanye, "
          f"{truncated} terpotong, {without_intent} tanpa intent")
    if skipped:
        print(f"dilewati ({len(skipped)}): {', '.join(skipped[:5])}")


def selfcheck():
    import tempfile

    root = Path(tempfile.mkdtemp())
    wrapped = root / "wrapped"
    capability.build_fixture(wrapped / "package", {"package.json": '{"name":"w"}'})
    assert package_root(wrapped) == wrapped / "package"
    flat = root / "flat"
    capability.build_fixture(flat, {"package.json": '{"name":"f"}'})
    assert package_root(flat) == flat, "a flat layout must be left alone"
    assert not has_content(root / "nothing") and has_content(flat)

    before, after = root / "v1", root / "v2"
    capability.build_fixture(before, {
        "package.json": '{"name":"p","version":"1","description":"A tiny helper"}',
        "index.js": "module.exports = 1;\n",
    })
    capability.build_fixture(after, {
        "package.json": '{"name":"p","version":"2","scripts":{"preinstall":"node s.js"}}',
        "index.js": "module.exports = 1;\n",
        "s.js": "require('https').request({host:'x.example'});\n",
    })

    # The same tree hashes the same wherever it was unpacked, and a changed file moves it.
    moved = root / "moved"
    capability.build_fixture(moved, {
        "package.json": '{"name":"p","version":"1","description":"A tiny helper"}',
        "index.js": "module.exports = 1;\n",
    })
    assert tree_digest(before) == tree_digest(moved), "digest depends on the path"
    assert tree_digest(before) != tree_digest(after)

    words = lambda text: len(text.split())  # noqa: E731
    row = build_row("p", "1", "2", before, after, "MAL", "test", words)
    assert row["id"] == "p@2" and row["label"] == "malicious"
    assert "install_script" in row["delta"] and "network" in row["delta"]
    assert row["intent_from"] == "1" and row["intent_available"]
    # The intent must come from the previous version, never leak the new one.
    assert "preinstall" not in json.dumps(row["intent"]), row["intent"]
    assert "s.js" in row["diff"] and row["gold_evidence"] == []

    print("ok")


if __name__ == "__main__":
    if "--selfcheck" in sys.argv:
        selfcheck()
    else:
        main()
