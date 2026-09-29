"""Reading a verdict out of a model reply."""
import json


# parse_verdict validates the first JSON object in the reply; extra keys are ignored.
def parse_verdict(text):
    # raw_decode reads one object, where slicing to the last brace breaks on prose containing "}".
    start = text.find("{")
    if start == -1:
        return None
    try:
        parsed, _ = json.JSONDecoder().raw_decode(text[start:])
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, dict):
        return None
    verdict = parsed.get("verdict")
    if not isinstance(verdict, str) or verdict.strip().lower() not in ("malicious", "benign"):
        return None
    evidence = parsed.get("evidence")
    if not isinstance(evidence, list) or not all(isinstance(item, str) for item in evidence):
        return None
    if not isinstance(parsed.get("reason"), str):
        return None
    return {"verdict": verdict.strip().lower(), "evidence": evidence, "reason": parsed["reason"]}
