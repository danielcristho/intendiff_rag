"""Batch runner for the IntentDiff-RAG experiments.

    python pipeline/runner.py --model Qwen/Qwen3-4B-Instruct-2507
    python pipeline/runner.py --selfcheck

Reads pairs.jsonl, runs every configuration against a vLLM server over its
OpenAI-compatible endpoint, and appends one result line per run to
results.jsonl. Safe to stop at any time: runs already present are skipped.

vLLM specifically, not Ollama (D46): D40 requires unquantized bfloat16, and
§9.3 reads the model weight memory from the vLLM log. Ollama serves quantized
GGUF by default, so it is only ever used to smoke-test pipeline mechanics.

GPU memory is not measured here. vLLM pre-allocates according to
--gpu-memory-utilization, so an nvidia-smi peak reflects that allocation rather
than the model's need; methodology §9.3 (D41) defines what to report instead.
"""
import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from prompts import CONFIGS, build  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


# load_jsonl parses one JSON value per non-blank line, or nothing if absent.
def load_jsonl(path):
    p = Path(path)
    if not p.exists():
        return []
    return [json.loads(line) for line in p.read_text().splitlines() if line.strip()]


# run_key identifies one run so a resumed batch can skip what is already done.
def run_key(model, config, pair_id, seed):
    # docs/experiments.md §4: must also carry the temperature, or the Stage 2
    # seed-0 run collides with Stage 1 and is silently skipped.
    return f"{model}|{config}|{pair_id}|{seed}"


# done_keys returns the run keys already recorded in a results file.
def done_keys(path):
    return {r["run_key"] for r in load_jsonl(path) if "run_key" in r}


# score measures capability-delta overlap between a pair and a card.
def score(pair_delta, card_delta):
    # Retrieval is keyed on the delta, not on text: a card with no delta never
    # outranks a real match, and a pair with no delta scores 0 everywhere.

    a, b = set(pair_delta or []), set(card_delta or [])
    union = a | b
    return len(a & b) / len(union) if union else 0.0


# retrieve selects the knowledge-base cards one configuration is given.
def retrieve(config, pair, kb):
    if config in ("E0", "E1") or not kb:
        return []
    ranked = sorted(kb, key=lambda c: -score(pair.get("delta"), c.get("delta")))
    if config == "E2":  # mixed KB, single nearest card
        return ranked[:1]
    if config == "E3":  # malicious only: the bias is deliberate, it is what E3 measures
        return [c for c in ranked if c["label"] == "malicious"][:1]
    # E4 is contrastive: one malicious card plus one benign look-alike.
    mal = [c for c in ranked if c["label"] == "malicious"][:1]
    ben = [c for c in ranked if c["label"] == "benign"][:1]
    return mal + ben


# parse_verdict extracts the first complete JSON object from a model reply.
def parse_verdict(text):
    # Models wrap JSON in prose. docs/methodology.md §7 replaces this with
    # raw_decode, which also survives prose containing a closing brace.
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        return None
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None


# call_llm sends one chat completion request, retrying with a backoff.
def call_llm(base_url, model, messages, seed, timeout, retries=3):
    payload = json.dumps({
        "model": model,
        "messages": messages,
        "temperature": 0,
        "seed": seed,
        "max_tokens": 512,
    }).encode()
    req = urllib.request.Request(
        f"{base_url.rstrip('/')}/v1/chat/completions",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    last = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as res:
                return json.loads(res.read())
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last = exc
            time.sleep(2**attempt)
    raise RuntimeError(f"failed after {retries} attempts: {last}")


# main runs every pending pair-configuration combination and records the results.
def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--base-url", default="http://localhost:8000")
    ap.add_argument("--pairs", default=str(ROOT / "data/pairs.jsonl"))
    ap.add_argument("--kb", default=str(ROOT / "data/kb.jsonl"))
    ap.add_argument("--out", default=str(ROOT / "data/results.jsonl"))
    ap.add_argument("--configs", default=",".join(CONFIGS))
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--timeout", type=float, default=120)
    ap.add_argument("--limit", type=int, help="cap the number of pairs, for smoke tests")
    args = ap.parse_args(argv)

    pairs = load_jsonl(args.pairs)[: args.limit]
    kb = load_jsonl(args.kb)
    configs = args.configs.split(",")
    if not pairs:
        sys.exit(f"no pairs found in {args.pairs}")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    already = done_keys(out)
    todo = [
        (p, c) for p in pairs for c in configs
        if run_key(args.model, c, p["id"], args.seed) not in already
    ]
    print(f"{len(pairs)} pairs x {len(configs)} configs · {len(already)} done · {len(todo)} to run")

    # ponytail: sequential on purpose. RQ4 reports median and p95 latency, and
    # those numbers are wrong if requests overlap on the server (methodology
    # §9.2). Add a parallel flag only when throughput matters more than latency.
    for i, (pair, config) in enumerate(todo, 1):
        messages = build(config, pair, retrieve(config, pair, kb))
        record = {
            "run_key": run_key(args.model, config, pair["id"], args.seed),
            "pair_id": pair["id"],
            "config": config,
            "model": args.model,
            "seed": args.seed,
            "label": pair.get("label"),
        }
        started = time.perf_counter()
        try:
            res = call_llm(args.base_url, args.model, messages, args.seed, args.timeout)
            text = res["choices"][0]["message"]["content"]
            parsed = parse_verdict(text)
            usage = res.get("usage", {})
            record.update({
                "verdict": (parsed or {}).get("verdict"),
                "evidence": (parsed or {}).get("evidence"),
                "reason": (parsed or {}).get("reason"),
                "json_valid": parsed is not None,
                "raw": text,
                "prompt_tokens": usage.get("prompt_tokens"),
                "completion_tokens": usage.get("completion_tokens"),
            })
        except Exception as exc:  # recorded, never aborts the batch
            record.update({"error": str(exc), "json_valid": False})

        record["latency_ms"] = round((time.perf_counter() - started) * 1000, 1)
        # Appended per run, so a crash keeps everything already completed.
        with out.open("a") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        print(f"[{i}/{len(todo)}] {config} {pair['id']} -> {record.get('verdict') or record.get('error')}")


# selfcheck asserts the resume, scoring and parsing rules without a live model.
def selfcheck():
    import tempfile

    tmp = Path(tempfile.mkdtemp())
    f = tmp / "r.jsonl"
    assert load_jsonl(f) == [], "a missing file reads as empty, not a crash"
    f.write_text('{"run_key":"m|E0|a|0"}\n\n{"run_key":"m|E1|a|0"}\n')
    assert done_keys(f) == {"m|E0|a|0", "m|E1|a|0"}, "resume keys misread"

    assert score(["x"], ["x"]) == 1.0
    assert score(["x"], ["y"]) == 0.0
    assert score([], []) == 0.0, "an empty delta must not divide by zero"
    assert score(["x", "y"], ["x"]) == 0.5

    kb = [
        {"id": "m1", "label": "malicious", "delta": ["a"]},
        {"id": "m2", "label": "malicious", "delta": ["z"]},
        {"id": "b1", "label": "benign", "delta": ["a"]},
    ]
    pair = {"id": "p", "delta": ["a"]}
    assert retrieve("E0", pair, kb) == []
    assert retrieve("E1", pair, kb) == [], "E1 uses a fixed demo, never retrieval"
    assert [c["id"] for c in retrieve("E2", pair, kb)] == ["m1"]
    assert [c["id"] for c in retrieve("E3", pair, kb)] == ["m1"]
    got = {c["label"] for c in retrieve("E4", pair, kb)}
    assert got == {"malicious", "benign"}, "E4 must be contrastive, got: " + str(got)
    assert retrieve("E4", pair, []) == [], "an empty KB must not crash retrieval"

    assert parse_verdict('bla {"verdict":"benign"} bla')["verdict"] == "benign"
    assert parse_verdict("tanpa json") is None
    assert parse_verdict('{"rusak": }') is None
    print("ok")


if __name__ == "__main__":
    if "--selfcheck" in sys.argv:
        selfcheck()
    else:
        main()
