"""Read batch similarity scores from the pinned offline Dolos tool."""
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path


def score_lookup(items):
    codes = [item["code"] for item in items if item.get("code", "").strip()]
    hashes = [hashlib.sha256(code.encode()).hexdigest() for code in codes]
    rows = [{"id": str(index), "code": code} for index, code in enumerate(codes)]
    scores = {}
    if len(rows) >= 2:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "items.jsonl"
            path.write_text("".join(json.dumps(row) + "\n" for row in rows))
            result = subprocess.run(["dolos-pairs", str(path)], capture_output=True, text=True,
                                    timeout=600, check=True)
            for pair in json.loads(result.stdout):
                score = pair["similarity"]
                if not isinstance(score, (int, float)) or not 0 <= score <= 1:
                    raise ValueError("Dolos returned an invalid similarity")
                scores[tuple(sorted((hashes[int(pair["left"])], hashes[int(pair["right"])])))] = score

    def lookup(left, right):
        if not left.strip() or not right.strip():
            return 0.0
        keys = tuple(sorted(hashlib.sha256(code.encode()).hexdigest() for code in (left, right)))
        return scores.get(keys, 0.0)
    return lookup
