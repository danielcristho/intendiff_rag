"""Split the Wyss typical-update lists into the TYP sample and the path-A pool.

    python pipeline/typical.py sample --popular popular.txt --random random.txt \
        --out data/typ.jsonl --pool data/pool.jsonl
    python pipeline/typical.py screen --pool data/pool.jsonl --out data/hn_candidates.jsonl
    python pipeline/typical.py --selfcheck
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import capability  # noqa: E402
from collect import SEED, HN_CATEGORIES, deterministic_draw, hash_order  # noqa: E402

TYP_PER_LIST = 50


def load_jsonl(path):
    p = Path(path)
    if not p.exists():
        return []
    return [json.loads(line) for line in p.read_text().splitlines() if line.strip()]


# read_list parses the upstream `path_before,path_after` lines (D57).
def read_list(path, group):
    rows = []
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        before, _, after = line.partition(",")
        rows.append({"group": group, "line": line,
                     "before_dir": before.strip(), "after_dir": after.strip()})
    return rows


# draw uses canonical identities when available; upstream paths are only a
# fallback for lists that have not yet been resolved to package versions.
def draw(entries, take=TYP_PER_LIST, seed=SEED):
    return deterministic_draw(entries, take, seed, key=lambda row: row.get("id", row["line"]))


# partition keeps the 50/50 popular-random mix of the source (§3.2).
def partition(popular, random_group, take=TYP_PER_LIST, seed=SEED):
    typ, queue = [], []
    for entries in (popular, random_group):
        drawn, rest = draw(entries, take, seed)
        typ.extend(drawn)
        queue.extend(rest)
    return typ, queue


# identity reads name and version from package.json, not from the path, because
# the directory layout inside the replication package is not verified yet (D57).
def identity(version_dir):
    manifest = capability.package_json(Path(version_dir)) or {}
    return manifest.get("name"), manifest.get("version")


# signal_categories lists the categories a delta could belong to. It screens
# candidates only: §3.3 decides the category from the documented purpose.
def signal_categories(delta):
    found = set(delta or [])
    return sorted(number for number, category in HN_CATEGORIES.items()
                  if found & category["signals"])


# screen_one returns a candidate row, or None when the update adds no capability.
def screen_one(entry):
    before, after = Path(entry["before_dir"]), Path(entry["after_dir"])
    delta = capability.delta(before, after)
    if not delta:
        return None
    name, version = identity(after)
    _, previous = identity(before)
    return {"name": name, "before": previous, "after": version,
            "source": "wyss-typical", "group": entry.get("group"),
            "before_dir": str(before), "after_dir": str(after),
            "delta": delta, "signal_categories": signal_categories(delta)}


# screen runs path A: every pool update through the extractor, non-empty delta wins.
def screen(pool):
    rows, empty, nameless = [], 0, 0
    for entry in pool:
        row = screen_one(entry)
        if row is None:
            empty += 1
            continue
        if not row["name"] or not row["after"]:
            nameless += 1
        rows.append(row)
    ordered = hash_order(rows, key=lambda row: (row["name"] or "", row["after"] or ""))
    return ordered, {"screened": len(pool), "candidates": len(rows),
                     "empty_delta": empty, "missing_identity": nameless}


def write_jsonl(path, rows):
    Path(path).write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows))


def main(argv=None):
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    split = sub.add_parser("sample", help="draw TYP and leave the rest as the path-A pool")
    split.add_argument("--popular", required=True, help="typical_updates_popular.txt")
    split.add_argument("--random", required=True, dest="random_list",
                       help="typical_updates_random.txt")
    split.add_argument("--take", type=int, default=TYP_PER_LIST, help="per list, §3.2 draws 50")
    split.add_argument("--out", required=True)
    split.add_argument("--pool", required=True)

    sift = sub.add_parser("screen", help="path A: keep the updates that add a capability")
    sift.add_argument("--pool", required=True)
    sift.add_argument("--out", required=True)

    args = parser.parse_args(argv)

    if args.command == "sample":
        typ, pool = partition(read_list(args.popular, "popular"),
                              read_list(args.random_list, "random"), args.take)
        write_jsonl(args.out, typ)
        write_jsonl(args.pool, pool)
        print(json.dumps({"typ": len(typ), "pool": len(pool)}))
        return

    rows, counts = screen(load_jsonl(args.pool))
    write_jsonl(args.out, rows)
    per_category = {number: sum(1 for row in rows if number in row["signal_categories"])
                    for number in sorted(HN_CATEGORIES)}
    print(json.dumps({**counts, "per_signal_category": per_category}))


def selfcheck():
    import tempfile

    tmp = Path(tempfile.mkdtemp())

    popular = [{"group": "popular", "line": f"a/{n}/before,a/{n}/after"} for n in range(120)]
    drawn, queue = draw(popular, take=50)

    # The partition is exact: nothing is lost and nothing appears twice.
    assert len(drawn) == 50 and len(queue) == 70
    assert {row["line"] for row in drawn} | {row["line"] for row in queue} == \
        {row["line"] for row in popular}
    assert not {row["line"] for row in drawn} & {row["line"] for row in queue}

    # Same seed, same pick — and the upstream line order cannot change it.
    again, _ = draw(list(reversed(popular)), take=50)
    assert [row["line"] for row in again] == [row["line"] for row in drawn]
    assert [row["line"] for row in draw(popular, take=50, seed=1)[0]] != \
        [row["line"] for row in drawn]

    identified = [dict(row, id=f"pkg-{i}@1.0.1") for i, row in enumerate(popular)]
    moved = [dict(row, line="different-root/" + row["line"]) for row in identified]
    assert [r["id"] for r in draw(identified)[0]] == [r["id"] for r in draw(moved)[0]]

    # §3.2 draws 50 from each list, so TYP is 100 with the mix kept.
    typ, pool = partition(popular, [dict(row, group="random") for row in popular])
    assert len(typ) == 100 and len(pool) == 140
    assert sum(1 for row in typ if row["group"] == "popular") == 50

    # A list file is read as `path_before,path_after`.
    (tmp / "list.txt").write_text("x/1.0.0,x/1.0.1\n\n y/2.0.0 , y/2.1.0 \n")
    rows = read_list(tmp / "list.txt", "popular")
    assert [(r["before_dir"], r["after_dir"]) for r in rows] == \
        [("x/1.0.0", "x/1.0.1"), ("y/2.0.0", "y/2.1.0")]

    # Signals screen, they do not assign: network belongs to two categories.
    assert signal_categories(["network"]) == [2, 4]
    assert signal_categories(["install_script"]) == [1]
    assert signal_categories([]) == []

    capability.build_fixture(tmp / "quiet/1.0.0", {
        "package.json": '{"name":"quiet","version":"1.0.0"}', "index.js": "module.exports = 1;\n"})
    capability.build_fixture(tmp / "quiet/1.0.1", {
        "package.json": '{"name":"quiet","version":"1.0.1"}', "index.js": "module.exports = 2;\n"})
    capability.build_fixture(tmp / "loud/2.0.0", {
        "package.json": '{"name":"loud","version":"2.0.0"}', "index.js": "module.exports = 1;\n"})
    capability.build_fixture(tmp / "loud/2.0.1", {
        "package.json": '{"name":"loud","version":"2.0.1"}',
        "index.js": "module.exports = 1;\n",
        "send.js": "require('https').request({host:'x'}).end();\n"})

    pool = [{"group": "popular", "line": "l1",
             "before_dir": str(tmp / "quiet/1.0.0"), "after_dir": str(tmp / "quiet/1.0.1")},
            {"group": "random", "line": "l2",
             "before_dir": str(tmp / "loud/2.0.0"), "after_dir": str(tmp / "loud/2.0.1")}]
    candidates, counts = screen(pool)

    # An update that adds no capability is not a hard-negative candidate.
    assert counts == {"screened": 2, "candidates": 1, "empty_delta": 1, "missing_identity": 0}
    candidate = candidates[0]

    # Identity comes from package.json, so an unverified path layout cannot break it.
    assert (candidate["name"], candidate["before"], candidate["after"]) == ("loud", "2.0.0", "2.0.1")
    assert candidate["delta"] == ["network"]
    assert candidate["signal_categories"] == [2, 4]

    print("ok")


if __name__ == "__main__":
    if "--selfcheck" in sys.argv:
        selfcheck()
    else:
        main()
