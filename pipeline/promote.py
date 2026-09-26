"""Promote approved KB cards to data/kb.jsonl, refusing if any card is not ready.

    python pipeline/promote.py
    python pipeline/promote.py --selfcheck
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import intent  # noqa: E402
from prompts import examples_block  # noqa: E402

SCHEMA = ("id", "name", "label", "campaign", "source", "delta",
          "intent", "behavior_chain", "code_excerpt", "rationale")
TEXT_FIELDS = ("intent", "behavior_chain", "code_excerpt", "rationale")
MAX_CARD_TOKENS = 512
MAX_INTENT_TOKENS = 64
MAX_EXCERPT_LINES = 15


# sample_lines collects every stripped line of the sample the card was written from.
def sample_lines(root):
    lines = set()
    for path in Path(root).rglob("*"):
        if path.is_file() and not path.is_symlink():
            text = path.read_bytes().decode("utf-8", errors="replace")
            lines.update(line.strip() for line in text.splitlines())
    return lines


# problems lists why one card cannot enter kb.jsonl; empty means it can.
def problems(row, entry, count, lines_of):
    if not entry or entry.get("stage") != "approved":
        return [f"stage {entry.get('stage') if entry else 'kosong'}, belum disetujui"]
    found = [f"{field} kosong" for field in TEXT_FIELDS if not entry.get(field, "").strip()]
    if found:
        return found

    excerpt = entry["code_excerpt"].splitlines()
    if len(excerpt) > MAX_EXCERPT_LINES:
        found.append(f"code_excerpt {len(excerpt)} baris > {MAX_EXCERPT_LINES}")
    # §5.1 requires the excerpt verbatim from the raw files; a line typed from
    # memory or tidied up would not be.
    known = lines_of(row["root"]) if row.get("root") else set()
    invented = [line for line in excerpt if line.strip() and line.strip() not in known]
    if invented:
        found.append(f"code_excerpt tidak verbatim: {invented[0].strip()[:60]!r}")

    if count(entry["intent"]) > MAX_INTENT_TOKENS:
        found.append(f"intent {count(entry['intent'])} token > {MAX_INTENT_TOKENS}")
    # Counted over the block the model is shown, which is what the budget limits.
    shown = count(examples_block([card(row, entry)]))
    if shown > MAX_CARD_TOKENS:
        found.append(f"card {shown} token > {MAX_CARD_TOKENS}; pangkas code_excerpt dulu")
    return found


def card(row, entry):
    merged = {**row, **{field: entry[field] for field in TEXT_FIELDS}}
    return {field: merged[field] for field in SCHEMA}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--skeleton", default="data/kb.skeleton.jsonl")
    parser.add_argument("--cards", default="data/kb.cards.json")
    parser.add_argument("--out", default="data/kb.jsonl")
    args = parser.parse_args(argv)

    rows = [json.loads(line) for line in Path(args.skeleton).read_text().splitlines() if line]
    cards_path = Path(args.cards)
    entries = json.loads(cards_path.read_text()) if cards_path.exists() else {}
    count = intent.qwen_counter()
    data_dir = Path(args.skeleton).parent
    cache = {}

    def lines_of(root):
        if root not in cache:
            cache[root] = sample_lines(data_dir / root)
        return cache[root]

    failures = {row["id"]: problems(row, entries.get(row["id"]), count, lines_of) for row in rows}
    failures = {card_id: found for card_id, found in failures.items() if found}
    if failures:
        # A partial kb.jsonl would be picked up silently by the runner.
        print(f"{len(failures)} dari {len(rows)} card belum siap; kb.jsonl tidak ditulis")
        for card_id, found in failures.items():
            print(f"  {card_id}: {'; '.join(found)}")
        sys.exit(1)

    out = Path(args.out)
    with out.open("w") as handle:
        for row in rows:
            handle.write(json.dumps(card(row, entries[row["id"]])) + "\n")
    print(f"{out}: {len(rows)} card")


def selfcheck():
    import tempfile

    with tempfile.TemporaryDirectory() as work:
        (Path(work) / "index.js").write_text("const a = 1;\n  fetch(url);\n")
        row = {"id": "c", "name": "p", "label": "malicious", "campaign": "c", "source": "datadog",
               "delta": ["network"], "root": work, "delta_evidence": {}, "selected_for": "network"}
        good = {"stage": "approved", "intent": "Claims to be a helper.", "behavior_chain": "a -> b",
                "code_excerpt": "fetch(url);", "rationale": "Sends data."}
        count = lambda text: len(text.split())  # noqa: E731
        lines_of = sample_lines

        assert problems(row, good, count, lines_of) == []
        # Only an approved card may enter the KB the runner reads.
        assert problems(row, {**good, "stage": "submitted"}, count, lines_of)
        assert problems(row, None, count, lines_of)
        # An excerpt line absent from the sample is not verbatim.
        assert any("verbatim" in p for p in problems(row, {**good, "code_excerpt": "fetch(evil);"},
                                                     count, lines_of))
        assert any("baris" in p for p in problems(
            row, {**good, "code_excerpt": "\n".join(["fetch(url);"] * 16)}, count, lines_of))
        assert any("intent" in p for p in problems(row, {**good, "intent": "w " * 65}, count, lines_of))
        # The promoted card carries the schema fields only, never the annotator aids.
        assert set(card(row, good)) == set(SCHEMA)
    print("promote selfcheck ok")


if __name__ == "__main__":
    if "--selfcheck" in sys.argv:
        selfcheck()
    else:
        main()
