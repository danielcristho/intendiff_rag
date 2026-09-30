"""Batch runner against a vLLM server.

    python pipeline/runner.py --model Qwen/Qwen2.5-Coder-3B-Instruct
    python pipeline/runner.py --selfcheck

Resumable: runs already in results.jsonl are skipped.
"""
import argparse
import hashlib
import json
import sys
import time
import urllib.error
import urllib.request
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from configs import CONFIGS, spec  # noqa: E402
from prompts import build  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


# load_jsonl parses one JSON value per non-blank line, or nothing if absent.
def load_jsonl(path):
    p = Path(path)
    if not p.exists():
        return []
    return [json.loads(line) for line in p.read_text().splitlines() if line.strip()]


# Identifies one run for the resume check.
def run_key(model, config, pair_id, seed, temperature):
    # Temperature belongs in the key: seed 0 is reused at another temperature
    # and would otherwise collide and be skipped.
    return f"{model}|{config}|{pair_id}|{seed}|{temperature}|max_tokens=2048|experiment=model-scale-20260930"


# A resume skips these.
def done_keys(path):
    # A transport error is not a result and must be retried; an invalid model
    # reply is one, and stays done. Without the split one blip loses runs.
    return {
        row["run_key"]
        for row in load_jsonl(path)
        if "run_key" in row and not row.get("error")
    }


# score measures capability-delta overlap between a pair and a card.
def score(pair_delta, card_delta):
    # Keyed on the delta, not on text.
    a, b = set(pair_delta or []), set(card_delta or [])
    union = a | b
    return len(a & b) / len(union) if union else 0.0


# eligible reports whether a card may be shown for this pair.
def eligible(pair, card):
    # Same package or campaign leaks the answer into the prompt.
    for field in ("name", "campaign"):
        if pair.get(field) and pair.get(field) == card.get(field):
            return False
    return True


# rank orders eligible cards by score, breaking ties deterministically.
def rank(pair, kb):
    # Ten signals means frequent ties; hashing keeps the winner independent
    # of the order kb.jsonl happens to be written in.
    def key(card):
        tiebreak = hashlib.sha256(f"{pair.get('id')}|{card.get('id')}".encode()).hexdigest()
        return (-score(pair.get("delta"), card.get("delta")), tiebreak)

    return sorted((card for card in kb if eligible(pair, card)), key=key)


# _ordered places the best malicious card first or second, per the pair's hash.
def _ordered(pair_id, primary, secondary):
    # Counterbalanced so the two configurations differ only in the second card.
    if secondary is None:
        return [primary]
    return [primary, secondary] if zlib.crc32(str(pair_id).encode()) % 2 == 0 else [secondary, primary]


# retrieve selects the knowledge-base cards one configuration is given, in prompt order.
def retrieve(config, pair, kb):
    wanted = spec(config).cards
    if not wanted or not kb:
        return []

    ranked = rank(pair, kb)
    chosen, taken = [], set()
    for label in wanted:
        # A label with no card left is skipped, so a thin pool degrades to fewer
        # cards rather than repeating one.
        pick = next((i for i, card in enumerate(ranked)
                     if i not in taken and card.get("label") == label), None)
        if pick is None:
            continue
        taken.add(pick)
        chosen.append(ranked[pick])

    if not chosen:
        return []
    return _ordered(pair.get("id"), chosen[0], chosen[1] if len(chosen) > 1 else None)


def retrieval_log(pair, cards):
    return [
        {
            "id": card.get("id"),
            "label": card.get("label"),
            "score": round(score(pair.get("delta"), card.get("delta")), 4),
            "position": position,
        }
        for position, card in enumerate(cards, start=1)
    ]


# parse_verdict returns the first complete JSON object of a reply, if it is valid.
def parse_verdict(text):
    # raw_decode reads ONE object; slicing to the last brace breaks on prose
    # containing "}".
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

    # Extra keys are ignored, not rejected.
    return {"verdict": verdict.strip().lower(), "evidence": evidence, "reason": parsed["reason"]}


# call_llm sends one chat completion request, retrying with a backoff.
def call_llm(base_url, model, messages, seed, timeout, sampling, retries=3):
    payload = json.dumps({
        "model": model,
        "messages": messages,
        "seed": seed,
        "max_tokens": 2048,
        **sampling,
        **({"chat_template_kwargs": {"enable_thinking": False}}
           if model == "Qwen/Qwen3-8B" else {}),
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
        # OSError, not URLError: ConnectionResetError is an OSError only, and
        # a narrower clause let the most retryable failure escape unretried.
        except (OSError, json.JSONDecodeError) as exc:
            last = exc
            time.sleep(2**attempt)
    raise RuntimeError(f"failed after {retries} attempts: {last}")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--base-url", default="http://localhost:8101")
    ap.add_argument("--pairs", default=str(ROOT / "data/pairs.jsonl"))
    ap.add_argument("--kb", default=str(ROOT / "data/kb.jsonl"))
    ap.add_argument("--out", default=str(ROOT / "data/results.jsonl"))
    ap.add_argument("--configs", default=",".join(CONFIGS))
    ap.add_argument("--seed", type=int, default=0)
    # Defaults are greedy; the sampling values come from the Qwen model card.
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--top-p", type=float, default=1.0)
    ap.add_argument("--top-k", type=int)
    ap.add_argument("--timeout", type=float, default=120)
    ap.add_argument("--limit", type=int, help="cap the number of pairs, for smoke tests")
    args = ap.parse_args(argv)

    pairs_path, kb_path = Path(args.pairs), Path(args.kb)
    pairs = load_jsonl(pairs_path)[: args.limit]
    kb = load_jsonl(kb_path)
    configs = args.configs.split(",")
    if not pairs:
        sys.exit(f"no pairs found in {pairs_path}")
    if any(spec(config).cards for config in configs) and not kb:
        sys.exit(f"retrieval configurations require a nonempty KB: {kb_path}")

    sampling = {"temperature": args.temperature, "top_p": args.top_p}
    if args.top_k is not None:
        sampling["top_k"] = args.top_k

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    already = done_keys(out)
    todo = [
        (pair, config)
        for pair in pairs
        for config in configs
        if run_key(args.model, config, pair["id"], args.seed, args.temperature) not in already
    ]
    # Record the explicit inputs; missing research data never selects a fixture.
    print(f"pairs={pairs_path.name} kb={kb_path.name} temp={args.temperature}")
    print(f"{len(pairs)} pairs x {len(configs)} configs · {len(already)} done · {len(todo)} to run")

    # ponytail: sequential on purpose — overlapping requests distort the
    # latency figures. Add a parallel flag when throughput matters more.
    for i, (pair, config) in enumerate(todo, 1):
        cards = retrieve(config, pair, kb)
        messages = build(config, pair, cards)
        record = {
            "run_key": run_key(args.model, config, pair["id"], args.seed, args.temperature),
            "pair_id": pair["id"],
            "config": config,
            "model": args.model,
            "seed": args.seed,
            "temperature": args.temperature,
            "top_p": args.top_p,
            "top_k": args.top_k,
            "max_tokens": 2048,
            "experiment_id": "model-scale-20260930",
            "chat_template_kwargs": ({"enable_thinking": False}
                                     if args.model == "Qwen/Qwen3-8B" else {}),
            "prompt_messages_sha256": hashlib.sha256(json.dumps(messages).encode()).hexdigest(),
            "label": pair.get("label"),
            "truncated": pair.get("truncated"),
            "cards": retrieval_log(pair, cards),
        }
        for field in ("evaluation_scope", "label_origin", "human_annotation_verified", "diff_sha256"):
            if field in pair:
                record[field] = pair[field]
        started = time.perf_counter()
        try:
            res = call_llm(args.base_url, args.model, messages, args.seed, args.timeout, sampling)
            choice = res["choices"][0]
            text = choice["message"]["content"]
            parsed = parse_verdict(text)
            usage = res.get("usage", {})
            # A truncated reply is invalid however well-formed the fragment looks.
            finish_reason = choice.get("finish_reason")
            valid = parsed is not None and finish_reason != "length"
            record.update({
                "verdict": (parsed or {}).get("verdict"),
                "evidence": (parsed or {}).get("evidence"),
                "reason": (parsed or {}).get("reason"),
                "json_valid": valid,
                "finish_reason": finish_reason,
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


def selfcheck():
    import tempfile

    tmp = Path(tempfile.mkdtemp())
    f = tmp / "r.jsonl"
    assert load_jsonl(f) == [], "a missing file reads as empty, not a crash"
    f.write_text('{"run_key":"m|DIFF+I|a|0|0.0"}\n\n{"run_key":"m|DIFF|a|0|0.0"}\n')
    assert done_keys(f) == {"m|DIFF+I|a|0|0.0", "m|DIFF|a|0|0.0"}, "resume keys misread"

    # A row that failed to reach the server must be retried, not skipped.
    failed = tmp / "err.jsonl"
    failed.write_text(
        '{"run_key":"m|DIFF+I|a|0|0.0","error":"connection refused"}\n'
        '{"run_key":"m|DIFF+I+MB|a|0|0.0","verdict":"benign"}\n'
        '{"run_key":"m|DIFF+I+M|a|0|0.0","verdict":null,"json_valid":false}\n'
    )
    # The invalid-output row still counts as done: D18 scores it as benign.
    assert done_keys(failed) == {"m|DIFF+I+MB|a|0|0.0", "m|DIFF+I+M|a|0|0.0"}, done_keys(failed)

    # Stage 2 reuses seed 0 at a different temperature, so the keys must differ
    # or those 3,000 runs are silently skipped (§4).
    assert run_key("m", "DIFF+I", "a", 0, 0.0) != run_key("m", "DIFF+I", "a", 0, 0.7)

    assert score(["x"], ["x"]) == 1.0
    assert score(["x"], ["y"]) == 0.0
    assert score([], []) == 0.0, "an empty delta must not divide by zero"
    assert score(["x", "y"], ["x"]) == 0.5

    kb = [
        {"id": "m1", "label": "malicious", "delta": ["network"], "campaign": "c1", "name": "a"},
        {"id": "m2", "label": "malicious", "delta": ["network"], "campaign": "c2", "name": "b"},
        {"id": "b1", "label": "benign", "delta": ["network"], "campaign": "c3", "name": "c"},
    ]
    pair = {"id": "p1", "name": "z", "campaign": "c9", "delta": ["network"]}

    assert retrieve("DIFF+I", pair, kb) == []
    assert retrieve("DIFF", pair, kb) == []
    assert retrieve("DIFF+I+MB", pair, []) == [], "an empty KB must not crash retrieval"

    # A card from the same package or campaign would leak the answer (D13).
    same_campaign = dict(pair, campaign="c1")
    assert all(card["id"] != "m1" for card in rank(same_campaign, kb))
    same_name = dict(pair, name="b")
    assert all(card["id"] != "m2" for card in rank(same_name, kb))

    # Ties break on a hash, so the order of kb.jsonl cannot decide the winner (D34).
    assert [c["id"] for c in rank(pair, kb)] == [c["id"] for c in rank(pair, list(reversed(kb)))]

    # DIFF+MB must receive exactly the same cards and order as DIFF+I+MB.
    assert {c["label"] for c in retrieve("DIFF+I+MB", pair, kb)} == {"malicious", "benign"}
    assert retrieve("DIFF+I+MB", pair, kb) == retrieve("DIFF+MB", pair, kb)

    # D42: the top malicious card sits at the same position in DIFF+I+MM and DIFF+I+MB, so
    # the two differ only in their second card.
    top = retrieve("DIFF+I+M", pair, kb)[0]["id"]
    for config in ("DIFF+I+MM", "DIFF+I+MB"):
        cards = retrieve(config, pair, kb)
        assert len(cards) == 2, config
        assert [c["id"] for c in cards].index(top) == \
            [c["id"] for c in retrieve("DIFF+I+MM", pair, kb)].index(top), config

    # Counterbalancing actually swaps: some pair id must put the malicious card
    # first and another must put it second.
    positions = set()
    for n in range(12):
        cards = retrieve("DIFF+I+MB", dict(pair, id=f"p{n}"), kb)
        positions.add(next(i for i, c in enumerate(cards) if c["label"] == "malicious"))
    assert positions == {0, 1}, positions

    # With a single malicious card and no benign one, DIFF+I+MM degrades to one card.
    only_one = [kb[0]]
    assert len(retrieve("DIFF+I+MM", pair, only_one)) == 1

    log = retrieval_log(pair, retrieve("DIFF+I+MB", pair, kb))
    assert [entry["position"] for entry in log] == [1, 2], log
    assert all(entry["score"] == 1.0 for entry in log), log

    ok = '{"evidence":["+x"],"reason":"r","verdict":"benign"}'
    assert parse_verdict(f"Here it is: {ok}")["verdict"] == "benign"
    assert parse_verdict("no json here") is None
    assert parse_verdict('{"broken": }') is None

    # The old slice-to-last-brace parser broke here: prose after the object
    # containing a closing brace swallowed it (§7).
    assert parse_verdict(f'{ok}\nNote: the object {{...}} above is my answer.') is not None

    # §7 validity: the verdict must be one of the two words, evidence a list of
    # strings, and reason a string. Anything else is an invalid output (D18).
    assert parse_verdict('{"evidence":[],"reason":"r","verdict":"MALICIOUS "}')["verdict"] == "malicious"
    assert parse_verdict('{"evidence":[],"reason":"r","verdict":"suspicious"}') is None
    assert parse_verdict('{"evidence":"+x","reason":"r","verdict":"benign"}') is None
    assert parse_verdict('{"evidence":[1],"reason":"r","verdict":"benign"}') is None
    assert parse_verdict('{"evidence":[],"verdict":"benign"}') is None
    # Extra keys are ignored rather than rejected.
    assert parse_verdict('{"evidence":[],"reason":"r","verdict":"benign","extra":1}') is not None

    # A connection reset must be retried. It is an OSError but not a URLError,
    # so the narrower clause this replaced skipped the backoff entirely.
    attempts = []

    def refuse(*_args, **_kwargs):
        attempts.append(1)
        raise ConnectionResetError(104, "Connection reset by peer")

    real_urlopen, real_sleep = urllib.request.urlopen, time.sleep
    urllib.request.urlopen, time.sleep = refuse, lambda _seconds: None
    try:
        call_llm("http://x", "m", [], 0, 1, {"temperature": 0})
    except RuntimeError as exc:
        assert "failed after 3 attempts" in str(exc), exc
    else:
        raise AssertionError("a reset must surface as a failure, not a result")
    finally:
        urllib.request.urlopen, time.sleep = real_urlopen, real_sleep
    assert len(attempts) == 3, f"retried {len(attempts)} times, expected 3"

    print("ok")


if __name__ == "__main__":
    if "--selfcheck" in sys.argv:
        selfcheck()
    else:
        main()
