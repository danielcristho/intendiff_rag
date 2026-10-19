"""Assemble pairs.jsonl from extracted version directories.

    python pipeline/dataset.py --manifest data/pairs.manifest.jsonl --out data/pairs.jsonl
    python pipeline/dataset.py --selfcheck
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import capability  # noqa: E402
import intent as intent_builder  # noqa: E402
import smartdiff  # noqa: E402

# §3 field order, so a hand-read line stays predictable.
CARRIED = ("id", "name", "before", "after", "subset", "category",
           "campaign", "source", "published_at", "group", "evaluation_scope", "label_provenance")
VERDICTS = ("id", "label", "gold_evidence")


def load_jsonl(path):
    p = Path(path)
    if not p.exists():
        return []
    return [json.loads(line) for line in p.read_text().splitlines() if line.strip()]


# checksum_index keys samples.jsonl the way a manifest entry names a version.
def checksum_index(samples):
    return {(row.get("name"), row.get("version")): row.get("sha256") for row in samples}


# build_row composes the per-pair tools. The diff is cut once here, never in the
# runner: §4.5 requires every configuration and both models to read the same text.
def build_row(entry, count, checksums=None):
    before, after = Path(entry["before_dir"]), Path(entry["after_dir"])
    checksums = checksums or {}

    diff = smartdiff.build(before, after, count)
    profile = intent_builder.build(before, count)

    row = {key: entry[key] for key in CARRIED if key in entry}
    for side in ('before', 'after'):
        field = 'sha256_' + side
        indexed = checksums.get((entry.get('name'), entry.get(side)))
        if indexed and entry.get(field) and indexed != entry[field]:
            raise ValueError('Conflicting archive checksum: ' + field)
        # Preserve acquisition hashes when no separate checksum index is supplied.
        row[field] = indexed or entry.get(field)
    # Intent comes from v_(t-1) only: the attacker controls v_t (D14).
    row["intent"] = profile
    row["intent_available"] = intent_builder.available(profile)
    row["intent_from"] = entry.get("before")
    row["delta"] = capability.delta(before, after)
    row["delta_evidence"] = capability.delta_evidence(before, after)
    row["diff"] = diff["diff"]
    row["truncated"] = diff["truncated"]
    row["preprocessing"] = diff.get("preprocessing", {"version": "test-only"})
    for key in VERDICTS[1:]:
        if key in entry:
            row[key] = entry[key]
    return row


# order keeps the file reproducible whatever order the manifest happens to be in.
def order(rows):
    return sorted(rows, key=lambda row: hashlib.sha256(
        f"{row.get('name')}@{row.get('after')}".encode()).hexdigest())


# assemble reports the skipped pairs too, because §8 requires that count.
def assemble(manifest, count, checksums=None):
    rows, skipped = [], 0
    for entry in manifest:
        if entry.get("label") == "skip":
            skipped += 1
            continue
        rows.append(build_row(entry, count, checksums))
    return order(rows), skipped


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True,
                        help="one line per pair: before_dir, after_dir, and the §3 metadata")
    parser.add_argument("--samples", help="samples.jsonl, for the tarball checksums")
    parser.add_argument("--out", required=True)
    parser.add_argument("--budget", type=int, default=smartdiff.BUDGET_TOKENS)
    parser.add_argument("--approx", action="store_true",
                        help="count 4 characters per token instead of loading the tokenizer")
    args = parser.parse_args(argv)

    count = (lambda text: len(text) // 4) if args.approx else smartdiff.qwen_counter()
    rows, skipped = assemble(load_jsonl(args.manifest), count,
                             checksum_index(load_jsonl(args.samples)) if args.samples else None)

    Path(args.out).write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows))
    truncated = sum(1 for row in rows if row["truncated"])
    print(json.dumps({"pairs": len(rows), "skipped": skipped, "truncated": truncated,
                      "no_intent": sum(1 for row in rows if not row["intent_available"])}))


def check_assembly():
    import tempfile

    tmp = Path(tempfile.mkdtemp())
    count = lambda text: len(text) // 4  # noqa: E731 - the --approx counter

    capability.build_fixture(tmp / "a/1.0.0", {
        "package.json": '{"name":"a","version":"1.0.0","description":"A formatter"}',
        "README.md": "# a\n\nFormats files.\n",
        "index.js": "module.exports = 1;\n",
    })
    capability.build_fixture(tmp / "a/1.0.1", {
        "package.json": '{"name":"a","version":"1.0.1","scripts":{"postinstall":"node s.js"}}',
        "README.md": "# a\n\nSECOND VERSION README.\n",
        "index.js": "module.exports = 1;\n",
        "s.js": "require('https').request({host:'x'});\n",
    })

    manifest = [{
        "id": "a@1.0.1", "name": "a", "before": "1.0.0", "after": "1.0.1",
        "subset": "MAL", "campaign": "demo", "source": "fixture",
        "published_at": "2026-01-01", "label": "malicious",
        "gold_evidence": ["+require('https').request({host:'x'});"],
        "before_dir": str(tmp / "a/1.0.0"), "after_dir": str(tmp / "a/1.0.1"),
    }]
    samples = [{"name": "a", "version": "1.0.0", "sha256": "aa"},
               {"name": "a", "version": "1.0.1", "sha256": "bb"}]

    rows, skipped = assemble(manifest, count, checksum_index(samples))
    assert skipped == 0
    row = rows[0]

    # Every field experiments.md §3 lists must be present, or the runner and the
    # backend read a hole.
    for field in ("id", "name", "before", "after", "subset", "campaign", "source",
                  "published_at", "sha256_before", "sha256_after", "intent",
                  "intent_available", "intent_from", "delta", "delta_evidence",
                  "diff", "truncated", "label", "gold_evidence"):
        assert field in row, field

    assert (row["sha256_before"], row["sha256_after"]) == ("aa", "bb")

    # The intent profile is read from v_(t-1), never from the version under review.
    assert row["intent_from"] == "1.0.0"
    assert "SECOND VERSION" not in json.dumps(row["intent"])
    assert row["intent_available"] is True

    # The delta is the capability that v_t added, and it carries its evidence.
    assert set(row["delta"]) >= {"network", "install_script"}, row["delta"]
    assert row["delta_evidence"], "the UI needs the evidence behind each signal"

    # The smart-diff reaches the row already cut, so the runner never recuts it.
    assert "s.js" in row["diff"] and row["truncated"] is False

    # §8: a pair the annotators could not agree on leaves the test set, counted.
    _, skipped = assemble([dict(manifest[0], label="skip")], count)
    assert skipped == 1

    # Order follows the hash of name@version, not the manifest order (§3).
    many = [dict(manifest[0], id=f"a@1.0.{n}", after=f"1.0.{n}") for n in (1, 2, 3)]
    forward, _ = assemble(many, count)
    backward, _ = assemble(list(reversed(many)), count)
    assert [r["id"] for r in forward] == [r["id"] for r in backward]

    print("ok")


def selfcheck():
    from unittest.mock import patch
    # Assembly checks are independent of the separately tested Node toolchain.
    with patch.object(smartdiff, "build", smartdiff.build_prepared):
        check_assembly()


if __name__ == "__main__":
    if "--selfcheck" in sys.argv:
        selfcheck()
    else:
        main()
