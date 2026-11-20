"""Fuzzes parse_verdict, which reads untrusted model output.

    uv run --with atheris==3.1.0 pipeline/fuzz_parse_verdict.py -max_total_time=60
"""
import sys

import atheris

with atheris.instrument_imports():
    from runner import parse_verdict

# Raw bytes almost never form JSON, so most inputs are assembled from these tokens.
TOKENS = ['{', '}', '[', ']', ':', ',', ' ', '"verdict"', '"evidence"', '"reason"',
          '"malicious"', '"benign"', '" Benign "', '"x"', '1', 'null', 'true', '\\', 'Answer: ']


def text_from(data):
    fdp = atheris.FuzzedDataProvider(data)
    parts = []
    while fdp.remaining_bytes():
        if fdp.ConsumeBool():
            token = TOKENS[fdp.ConsumeIntInRange(0, len(TOKENS) - 1)]
            parts.append(token * fdp.ConsumeIntInRange(1, 20_000 if token == '[' else 3))
        else:
            parts.append(fdp.ConsumeUnicodeNoSurrogates(fdp.ConsumeIntInRange(0, 16)))
    return ''.join(parts)


def test_one(data):
    parsed = parse_verdict(text_from(data))
    if parsed is None:
        return
    assert parsed["verdict"] in ("malicious", "benign")
    assert isinstance(parsed["evidence"], list) and all(isinstance(e, str) for e in parsed["evidence"])
    assert isinstance(parsed["reason"], str)


if __name__ == "__main__":
    atheris.Setup(sys.argv, test_one)
    atheris.Fuzz()
