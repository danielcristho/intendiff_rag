"""Write kb.jsonl from the approved cards, refusing while any card is not ready; runs offline."""
import argparse
import json
import sys
from pathlib import Path

from pipeline.datasets.kb.cards import TEXT_FIELDS, card
from pipeline.experiment.prompts import examples_block
from pipeline.shared.config import layout
from pipeline.shared.isolation import require_offline
from pipeline.shared.jsonl import read_jsonl, write_jsonl
from pipeline.shared.tokens import qwen_counter

MAX_CARD_TOKENS = 512
MAX_INTENT_TOKENS = 64
MAX_EXCERPT_LINES = 15


# sample_lines collects every stripped line of the sample a card was written from.
def sample_lines(root):
    lines = set()
    for path in Path(root).rglob("*"):
        if path.is_file() and not path.is_symlink():
            lines.update(line.strip() for line in path.read_bytes().decode("utf-8", errors="replace").splitlines())
    return lines


# problems lists why one card cannot enter kb.jsonl; empty means it can.
def problems(row, entry, count, lines_of):
    if not entry or entry.get("stage") != "approved":
        return [f"stage {entry.get('stage') if entry else 'empty'}, not approved"]
    found = [f"{field} is empty" for field in TEXT_FIELDS if not entry.get(field, "").strip()]
    if found:
        return found
    excerpt = entry["code_excerpt"].splitlines()
    if len(excerpt) > MAX_EXCERPT_LINES:
        found.append(f"code_excerpt has {len(excerpt)} lines, above {MAX_EXCERPT_LINES}")
    # The excerpt must be verbatim; a line typed from memory or tidied up is not in the sample.
    known = lines_of(row["root"]) if row.get("root") else set()
    invented = [line for line in excerpt if line.strip() and line.strip() not in known]
    if invented:
        found.append(f"code_excerpt is not verbatim: {invented[0].strip()[:60]!r}")
    if count(entry["intent"]) > MAX_INTENT_TOKENS:
        found.append(f"intent has {count(entry['intent'])} tokens, above {MAX_INTENT_TOKENS}")
    # The budget counts the block the model is shown.
    shown = count(examples_block([card(row, entry)]))
    if shown > MAX_CARD_TOKENS:
        found.append(f"card has {shown} tokens, above {MAX_CARD_TOKENS}; trim code_excerpt first")
    return found


def main(argv=None):
    argparse.ArgumentParser(prog="kb-promote").parse_args(argv)
    require_offline()
    data = layout()
    rows = read_jsonl(data.kb_skeleton)
    entries = json.loads(data.kb_cards.read_text()) if data.kb_cards.exists() else {}
    count, cache = qwen_counter(), {}

    def lines_of(root):
        if root not in cache:
            cache[root] = sample_lines(data / root)
        return cache[root]

    failures = {row["id"]: problems(row, entries.get(row["id"]), count, lines_of) for row in rows}
    failures = {card_id: found for card_id, found in failures.items() if found}
    if failures:
        # A partial kb.jsonl would be read by the runner without complaint.
        print(f"{len(failures)} of {len(rows)} cards are not ready; kb.jsonl not written")
        for card_id, found in failures.items():
            print(f"  {card_id}: {'; '.join(found)}")
        sys.exit(1)
    write_jsonl(data.kb, [card(row, entries[row["id"]]) for row in rows])
    print(f"{data.kb}: {len(rows)} cards")
