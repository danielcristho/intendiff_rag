"""Run configurations against the vLLM server and append one result row per run; resumable."""
import argparse
import sys
import time
from pathlib import Path

from pipeline.experiment.client import call_llm
from pipeline.experiment.parsing import parse_verdict
from pipeline.experiment.prompts import CONFIGS, build
from pipeline.experiment.retrieval import retrieval_log, retrieve
from pipeline.shared.config import layout, vllm_url
from pipeline.shared.jsonl import append_jsonl, read_jsonl

WARMUP_REQUESTS = 3


# existing_or_sample falls back to the fixture next to a missing dataset, as the backend does.
def existing_or_sample(path):
    real = Path(path)
    if real.exists():
        return real
    sample = real.with_name(real.name.replace(".jsonl", ".sample.jsonl"))
    return sample if sample.exists() else real


# run_key includes the temperature, since seed 0 recurs at another temperature.
def run_key(model, config, pair_id, seed, temperature):
    return f"{model}|{config}|{pair_id}|{seed}|{temperature}"


# done_keys skips finished runs; a transport error is retried, an invalid reply is a result.
def done_keys(path):
    return {row["run_key"] for row in read_jsonl(path) if "run_key" in row and not row.get("error")}


def run_one(args, sampling, pair, config, kb):
    cards = retrieve(config, pair, kb)
    record = {"run_key": run_key(args.model, config, pair["id"], args.seed, args.temperature),
              "pair_id": pair["id"], "config": config, "model": args.model, "seed": args.seed,
              "temperature": args.temperature, "top_p": args.top_p, "top_k": args.top_k,
              "label": pair.get("label"), "truncated": pair.get("truncated"),
              "cards": retrieval_log(pair, cards)}
    started = time.perf_counter()
    try:
        reply = call_llm(args.base_url, args.model, build(config, pair, cards), args.seed, args.timeout, sampling)
        choice = reply["choices"][0]
        text = choice["message"]["content"]
        parsed = parse_verdict(text) or {}
        usage = reply.get("usage", {})
        # A reply cut at the token limit is invalid however well-formed the fragment looks.
        record.update({"verdict": parsed.get("verdict"), "evidence": parsed.get("evidence"),
                       "reason": parsed.get("reason"),
                       "json_valid": bool(parsed) and choice.get("finish_reason") != "length",
                       "finish_reason": choice.get("finish_reason"), "raw": text,
                       "prompt_tokens": usage.get("prompt_tokens"),
                       "completion_tokens": usage.get("completion_tokens")})
    except Exception as exc:  # recorded, so one failure does not abort the batch
        record.update({"error": str(exc), "json_valid": False})
    record["latency_ms"] = round((time.perf_counter() - started) * 1000, 1)
    return record


def main(argv=None):
    data = layout()
    parser = argparse.ArgumentParser(prog="run")
    parser.add_argument("--model", required=True)
    parser.add_argument("--base-url", default=None, help="defaults to localhost:VLLM_PORT from .env")
    parser.add_argument("--pairs", default=str(data.pairs))
    parser.add_argument("--kb", default=str(data.kb))
    parser.add_argument("--out", default=str(data.results))
    parser.add_argument("--configs", default=",".join(CONFIGS))
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--top-p", type=float, default=1.0)
    parser.add_argument("--top-k", type=int)
    parser.add_argument("--timeout", type=float, default=120)
    parser.add_argument("--limit", type=int, help="cap the number of pairs, for smoke tests")
    args = parser.parse_args(argv)
    args.base_url = args.base_url or vllm_url()

    pairs_path, kb_path = existing_or_sample(args.pairs), existing_or_sample(args.kb)
    pairs, kb, configs = read_jsonl(pairs_path)[: args.limit], read_jsonl(kb_path), args.configs.split(",")
    if not pairs:
        sys.exit(f"no pairs found in {pairs_path}")
    sampling = {"temperature": args.temperature, "top_p": args.top_p,
                **({"top_k": args.top_k} if args.top_k is not None else {})}
    already = done_keys(args.out)
    todo = [(pair, config) for pair in pairs for config in configs
            if run_key(args.model, config, pair["id"], args.seed, args.temperature) not in already]
    # The file names are printed so a fixture fallback cannot pass for a real run.
    print(f"pairs={pairs_path.name} kb={kb_path.name} temp={args.temperature}")
    print(f"{len(pairs)} pairs x {len(configs)} configs · {len(already)} done · {len(todo)} to run")

    # The first requests after a server start carry one-off initialisation, so they go unrecorded.
    for pair in read_jsonl(data.pairs_dev)[:WARMUP_REQUESTS] if todo else []:
        try:
            call_llm(args.base_url, args.model, build("E0", pair, []), args.seed, args.timeout, sampling)
        except RuntimeError as exc:
            print(f"warm-up failed: {exc}")

    # ponytail: sequential, since overlapping requests distort latency; add a parallel flag for throughput.
    for index, (pair, config) in enumerate(todo, 1):
        record = run_one(args, sampling, pair, config, kb)
        append_jsonl(args.out, record, ensure_ascii=False)
        print(f"[{index}/{len(todo)}] {config} {pair['id']} -> {record.get('verdict') or record.get('error')}")
