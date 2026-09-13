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
import hashlib
import json
import sys
import time
import urllib.error
import urllib.request
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from prompts import CONFIGS, build  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


# existing_or_sample prefers the real dataset and falls back to the fixture.
def existing_or_sample(path):
    # Mirrors backend/src/store.rs so both halves of the project agree on which
    # file they are reading before the M1-2 corpus exists.
    real = Path(path)
    if real.exists():
        return real
    sample = real.with_name(real.name.replace(".jsonl", ".sample.jsonl"))
    return sample if sample.exists() else real


# load_jsonl parses one JSON value per non-blank line, or nothing if absent.
def load_jsonl(path):
    p = Path(path)
    if not p.exists():
        return []
    return [json.loads(line) for line in p.read_text().splitlines() if line.strip()]


# run_key identifies one run so a resumed batch can skip what is already done.
def run_key(model, config, pair_id, seed, temperature):
    # The temperature belongs in the key: Stage 2 reuses seed 0, so without it
    # that run collides with Stage 1 and is silently skipped (§4).
    return f"{model}|{config}|{pair_id}|{seed}|{temperature}"


# done_keys returns the run keys that finished, so a resume can skip them.
def done_keys(path):
    # A transport error is not a result: the run has to be retried. An invalid
    # model output is different — D18 counts that as a benign verdict, so it
    # stays done. Without this split, one network blip marks runs done forever.
    return {
        row["run_key"]
        for row in load_jsonl(path)
        if "run_key" in row and not row.get("error")
    }


# score measures capability-delta overlap between a pair and a card.
def score(pair_delta, card_delta):
    # Retrieval is keyed on the delta, not on text: "look-alike" here means the
    # same capability, which a text embedding would not guarantee (§5.2).
    a, b = set(pair_delta or []), set(card_delta or [])
    union = a | b
    return len(a & b) / len(union) if union else 0.0


# eligible reports whether a card may be shown for this pair.
def eligible(pair, card):
    # A card from the same package or campaign would leak the answer into the
    # prompt, so it is excluded before ranking (§5.2, D13).
    for field in ("name", "campaign"):
        if pair.get(field) and pair.get(field) == card.get(field):
            return False
    return True


# rank orders eligible cards by score, breaking ties deterministically.
def rank(pair, kb):
    # With only ten signals, ties are common. Breaking them on a hash of the
    # pair and card ids keeps the choice independent of the order of kb.jsonl,
    # which would otherwise favour whichever card was written first (D34).
    def key(card):
        tiebreak = hashlib.sha256(f"{pair.get('id')}|{card.get('id')}".encode()).hexdigest()
        return (-score(pair.get("delta"), card.get("delta")), tiebreak)

    return sorted((card for card in kb if eligible(pair, card)), key=key)


# _ordered places the best malicious card first or second, per the pair's hash.
def _ordered(pair_id, primary, secondary):
    # Counterbalancing the slots removes recency bias, and keeps E3-k2 and E4
    # differing only in their second card (D16, D42).
    if secondary is None:
        return [primary]
    return [primary, secondary] if zlib.crc32(str(pair_id).encode()) % 2 == 0 else [secondary, primary]


# retrieve selects the knowledge-base cards one configuration is given, in prompt order.
def retrieve(config, pair, kb):
    if config in ("E0", "E0-noint") or not kb:
        return []

    ranked = rank(pair, kb)
    malicious = [card for card in ranked if card.get("label") == "malicious"]
    benign = [card for card in ranked if card.get("label") == "benign"]

    if config == "E2":  # nearest card of either label
        return ranked[:1]
    if config == "E3":  # one malicious card; the bias is what E3 measures
        return malicious[:1]
    if config == "E3-k2":  # two malicious cards, the control for example count
        return _ordered(pair.get("id"), *(malicious[:2] + [None])[:2]) if malicious else []
    # E4 and E4-noint are contrastive: one malicious plus one benign look-alike.
    if not malicious and not benign:
        return []
    primary = malicious[0] if malicious else benign[0]
    secondary = benign[0] if malicious and benign else None
    return _ordered(pair.get("id"), primary, secondary)


# retrieval_log records which cards were shown, with their score and position.
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
    # §7: read ONE object with raw_decode rather than slicing to the last brace,
    # which breaks as soon as the model writes prose containing "}".
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

    # Extra keys are ignored, not rejected: the decision rule is about the three
    # fields the analysis reads.
    return {"verdict": verdict.strip().lower(), "evidence": evidence, "reason": parsed["reason"]}


# call_llm sends one chat completion request, retrying with a backoff.
def call_llm(base_url, model, messages, seed, timeout, sampling, retries=3):
    payload = json.dumps({
        "model": model,
        "messages": messages,
        "seed": seed,
        "max_tokens": 512,
        **sampling,
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
    ap.add_argument("--base-url", default="http://localhost:8101")
    ap.add_argument("--pairs", default=str(ROOT / "data/pairs.jsonl"))
    ap.add_argument("--kb", default=str(ROOT / "data/kb.jsonl"))
    ap.add_argument("--out", default=str(ROOT / "data/results.jsonl"))
    ap.add_argument("--configs", default=",".join(CONFIGS))
    ap.add_argument("--seed", type=int, default=0)
    # §9.2: Stage 1 is greedy; Stage 2 (EA2) uses the Qwen3 model card's
    # recommended sampling, the same values for both models.
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--top-p", type=float, default=1.0)
    ap.add_argument("--top-k", type=int)
    ap.add_argument("--timeout", type=float, default=120)
    ap.add_argument("--limit", type=int, help="cap the number of pairs, for smoke tests")
    args = ap.parse_args(argv)

    pairs_path, kb_path = existing_or_sample(args.pairs), existing_or_sample(args.kb)
    pairs = load_jsonl(pairs_path)[: args.limit]
    kb = load_jsonl(kb_path)
    configs = args.configs.split(",")
    if not pairs:
        sys.exit(f"no pairs found in {pairs_path}")

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
    # Name the files out loud: falling back to the fixtures must never be
    # mistaken for a run over the real corpus.
    print(f"pairs={pairs_path.name} kb={kb_path.name} temp={args.temperature}")
    print(f"{len(pairs)} pairs x {len(configs)} configs · {len(already)} done · {len(todo)} to run")

    # ponytail: sequential on purpose. RQ4 reports median and p95 latency, and
    # those numbers are wrong if requests overlap on the server (methodology
    # §9.2). Add a parallel flag only when throughput matters more than latency.
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
            "label": pair.get("label"),
            "truncated": pair.get("truncated"),
            "cards": retrieval_log(pair, cards),
        }
        started = time.perf_counter()
        try:
            res = call_llm(args.base_url, args.model, messages, args.seed, args.timeout, sampling)
            choice = res["choices"][0]
            text = choice["message"]["content"]
            parsed = parse_verdict(text)
            usage = res.get("usage", {})
            # §7: output cut off by the token limit counts as invalid, however
            # well-formed the fragment happens to look.
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


# selfcheck asserts the resume, retrieval and parsing rules without a live model.
def selfcheck():
    import tempfile

    tmp = Path(tempfile.mkdtemp())
    f = tmp / "r.jsonl"
    assert load_jsonl(f) == [], "a missing file reads as empty, not a crash"
    f.write_text('{"run_key":"m|E0|a|0|0.0"}\n\n{"run_key":"m|E2|a|0|0.0"}\n')
    assert done_keys(f) == {"m|E0|a|0|0.0", "m|E2|a|0|0.0"}, "resume keys misread"

    # A row that failed to reach the server must be retried, not skipped.
    failed = tmp / "err.jsonl"
    failed.write_text(
        '{"run_key":"m|E0|a|0|0.0","error":"connection refused"}\n'
        '{"run_key":"m|E4|a|0|0.0","verdict":"benign"}\n'
        '{"run_key":"m|E3|a|0|0.0","verdict":null,"json_valid":false}\n'
    )
    # The invalid-output row still counts as done: D18 scores it as benign.
    assert done_keys(failed) == {"m|E4|a|0|0.0", "m|E3|a|0|0.0"}, done_keys(failed)

    # Stage 2 reuses seed 0 at a different temperature, so the keys must differ
    # or those 3,000 runs are silently skipped (§4).
    assert run_key("m", "E0", "a", 0, 0.0) != run_key("m", "E0", "a", 0, 0.7)

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

    assert retrieve("E0", pair, kb) == []
    assert retrieve("E0-noint", pair, kb) == []
    assert retrieve("E4", pair, []) == [], "an empty KB must not crash retrieval"

    # A card from the same package or campaign would leak the answer (D13).
    same_campaign = dict(pair, campaign="c1")
    assert all(card["id"] != "m1" for card in rank(same_campaign, kb))
    same_name = dict(pair, name="b")
    assert all(card["id"] != "m2" for card in rank(same_name, kb))

    # Ties break on a hash, so the order of kb.jsonl cannot decide the winner (D34).
    assert [c["id"] for c in rank(pair, kb)] == [c["id"] for c in rank(pair, list(reversed(kb)))]

    # E4 is contrastive; E4-noint must receive exactly the same cards and order,
    # so RQ3 measures only the intent block (§5.2 invariant).
    assert {c["label"] for c in retrieve("E4", pair, kb)} == {"malicious", "benign"}
    assert retrieve("E4", pair, kb) == retrieve("E4-noint", pair, kb)

    # D42: the top malicious card sits at the same position in E3-k2 and E4, so
    # the two differ only in their second card.
    top = retrieve("E3", pair, kb)[0]["id"]
    for config in ("E3-k2", "E4"):
        cards = retrieve(config, pair, kb)
        assert len(cards) == 2, config
        assert [c["id"] for c in cards].index(top) == \
            [c["id"] for c in retrieve("E3-k2", pair, kb)].index(top), config

    # Counterbalancing actually swaps: some pair id must put the malicious card
    # first and another must put it second.
    positions = set()
    for n in range(12):
        cards = retrieve("E4", dict(pair, id=f"p{n}"), kb)
        positions.add(next(i for i, c in enumerate(cards) if c["label"] == "malicious"))
    assert positions == {0, 1}, positions

    # With a single malicious card and no benign one, E3-k2 degrades to one card.
    only_one = [kb[0]]
    assert len(retrieve("E3-k2", pair, only_one)) == 1

    log = retrieval_log(pair, retrieve("E4", pair, kb))
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

    print("ok")


if __name__ == "__main__":
    if "--selfcheck" in sys.argv:
        selfcheck()
    else:
        main()
