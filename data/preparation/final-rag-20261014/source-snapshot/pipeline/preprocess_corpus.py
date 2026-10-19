"""Build review pairs from real sources inside the offline container.

    python pipeline/preprocess_corpus.py --manifest FILE --out FILE --workers 4
"""
import argparse
import faulthandler
import hashlib
import json
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import dataset
import normalization
from samples import load_jsonl

TOKENIZER = "data/upstream/tokenizer-qwen25/tokenizer.json"
_tokenizer = None


def count(text):
    global _tokenizer
    if _tokenizer is None:
        from tokenizers import Tokenizer
        _tokenizer = Tokenizer.from_file(TOKENIZER)
    return len(_tokenizer.encode(text).ids)


def build(entry):
    faulthandler.dump_traceback_later(60)
    try:
        row = dataset.build_row(entry, count)
        row["annotation_status"] = entry.get("annotation_status", "pending")
        row["source_label"] = entry.get("source_label")
        row["before_dir"], row["after_dir"] = entry["before_dir"], entry["after_dir"]
        row["diff_tokens"] = count(row["diff"])
        row["diff_sha256"] = hashlib.sha256(row["diff"].encode()).hexdigest()
        for key in ("advisory_before", "advisory_ids", "same_publisher", "publishers",
                    "signal_categories", "source_archive_sha256", "sha256_before_tarball",
                    "sha256_before_tree", "sha256_after_tree"):
            if key in entry:
                row[key] = entry[key]
        return row
    except Exception as exc:
        return {"id": entry["id"], "error": f"{type(exc).__name__}: {str(exc)[:500]}",
                "preprocessing": {"version": normalization.VERSION}}
    finally:
        faulthandler.cancel_dump_traceback_later()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    entries = load_jsonl(args.manifest)
    previous = load_jsonl(args.out)
    versions = {r.get("preprocessing", {}).get("version") for r in previous}
    if versions - {normalization.VERSION}:
        raise ValueError("output contains another preprocessing version; use a new path")
    completed = {r["id"] for r in previous if not r.get("error")}
    pending = [r for r in entries if r["id"] not in completed]
    with ProcessPoolExecutor(max_workers=args.workers) as workers, Path(args.out).open("a") as output:
        futures = [workers.submit(build, entry) for entry in pending]
        for index, future in enumerate(as_completed(futures), 1):
            row = future.result()
            output.write(json.dumps(row) + "\n")
            output.flush()
            if row.get("error") or index % 10 == 0 or index == len(pending):
                print(json.dumps({"completed": len(completed) + index, "total": len(entries),
                                  "id": row["id"], "error": row.get("error"),
                                  "fallback_files": row.get("preprocessing", {}).get("fallback_files")}), flush=True)


if __name__ == "__main__":
    main()
