"""Check that missing research inputs cannot silently start fixture inference.

    python pipeline/test_runner_inputs.py
"""
import tempfile
from pathlib import Path
from unittest.mock import patch

import runner


def main():
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        (root / "pairs.sample.jsonl").write_text('{"id":"fixture"}\n')
        arguments = ["--model", "unused", "--pairs", str(root / "pairs.jsonl"),
                     "--kb", str(root / "kb.jsonl"), "--out", str(root / "results.jsonl")]
        with patch.object(runner, "call_llm", side_effect=AssertionError("unexpected inference")):
            for message in ("no pairs found", "nonempty KB"):
                try:
                    runner.main(arguments)
                except SystemExit as exc:
                    assert message in str(exc)
                else:
                    raise AssertionError("missing input was accepted")
                assert not (root / "results.jsonl").exists()
                (root / "pairs.jsonl").write_text('{"id":"real"}\n')
    print("missing-input inference guards passed")


if __name__ == "__main__":
    main()
