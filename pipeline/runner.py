"""Runner batch eksperimen IntentDiff-RAG.

    python pipeline/runner.py --model Qwen/Qwen3-4B-Instruct-2507
    python pipeline/runner.py --selfcheck

Baca pairs.jsonl, jalankan tiap konfigurasi E0-E4 lewat endpoint
OpenAI-compatible (vLLM/Ollama), tulis satu baris hasil per run ke
results.jsonl. Aman dihentikan kapan saja: run yang sudah ada dilewati.

Peak VRAM tidak diukur di sini — itu satu angka per model yang dimuat, bukan
per request. Catat terpisah lewat nvidia-smi saat server model jalan.
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


def load_jsonl(path):
    p = Path(path)
    if not p.exists():
        return []
    return [json.loads(line) for line in p.read_text().splitlines() if line.strip()]


def run_key(model, config, pair_id, seed):
    return f"{model}|{config}|{pair_id}|{seed}"


def done_keys(path):
    return {r["run_key"] for r in load_jsonl(path) if "run_key" in r}


def score(pair_delta, card_delta):
    """Jaccard antar capability delta — kunci retrieval-nya delta, bukan teks.

    Card tanpa delta tidak pernah menang atas card yang benar-benar cocok, dan
    pair tanpa delta memberi skor 0 di semua card sehingga urutannya jatuh ke
    urutan KB (deterministik), bukan ke kandidat acak.
    """
    a, b = set(pair_delta or []), set(card_delta or [])
    union = a | b
    return len(a & b) / len(union) if union else 0.0


def retrieve(config, pair, kb):
    """Pilih card sesuai konfigurasi. E0/E1 tidak mengambil apa pun."""
    if config in ("E0", "E1") or not kb:
        return []
    ranked = sorted(kb, key=lambda c: -score(pair.get("delta"), c.get("delta")))
    if config == "E2":  # mixed KB, satu terdekat
        return ranked[:1]
    if config == "E3":  # malicious saja: sengaja bias, itu yang diukur
        return [c for c in ranked if c["label"] == "malicious"][:1]
    # E4 contrastive: satu malicious + satu benign look-alike
    mal = [c for c in ranked if c["label"] == "malicious"][:1]
    ben = [c for c in ranked if c["label"] == "benign"][:1]
    return mal + ben


def parse_verdict(text):
    """Model bisa membungkus JSON dengan prosa; ambil objek pertama yang utuh."""
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        return None
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None


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
    raise RuntimeError(f"gagal setelah {retries} percobaan: {last}")


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
    ap.add_argument("--limit", type=int, help="potong jumlah pair, untuk smoke test")
    args = ap.parse_args(argv)

    pairs = load_jsonl(args.pairs)[: args.limit]
    kb = load_jsonl(args.kb)
    configs = args.configs.split(",")
    if not pairs:
        sys.exit(f"tidak ada pair di {args.pairs}")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    already = done_keys(out)
    todo = [
        (p, c) for p in pairs for c in configs
        if run_key(args.model, c, p["id"], args.seed) not in already
    ]
    print(f"{len(pairs)} pair x {len(configs)} konfigurasi · {len(already)} sudah ada · {len(todo)} dikerjakan")

    # ponytail: sekuensial. RQ3 mengukur median dan p95 latency, dan angka itu
    # rusak kalau request saling tumpang tindih di server. Tambahkan flag
    # paralel hanya kalau nanti butuh throughput dan latency-nya diabaikan.
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
        except Exception as exc:  # dicatat, bukan menghentikan batch
            record.update({"error": str(exc), "json_valid": False})

        record["latency_ms"] = round((time.perf_counter() - started) * 1000, 1)
        # Ditulis dan di-flush per run: kalau mati di tengah, yang sudah jalan aman.
        with out.open("a") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        print(f"[{i}/{len(todo)}] {config} {pair['id']} -> {record.get('verdict') or record.get('error')}")


def selfcheck():
    import tempfile

    tmp = Path(tempfile.mkdtemp())
    f = tmp / "r.jsonl"
    assert load_jsonl(f) == [], "file belum ada = kosong, bukan crash"
    f.write_text('{"run_key":"m|E0|a|0"}\n\n{"run_key":"m|E1|a|0"}\n')
    assert done_keys(f) == {"m|E0|a|0", "m|E1|a|0"}, "resume key salah dibaca"

    assert score(["x"], ["x"]) == 1.0
    assert score(["x"], ["y"]) == 0.0
    assert score([], []) == 0.0, "delta kosong tidak boleh bagi nol"
    assert score(["x", "y"], ["x"]) == 0.5

    kb = [
        {"id": "m1", "label": "malicious", "delta": ["a"]},
        {"id": "m2", "label": "malicious", "delta": ["z"]},
        {"id": "b1", "label": "benign", "delta": ["a"]},
    ]
    pair = {"id": "p", "delta": ["a"]}
    assert retrieve("E0", pair, kb) == []
    assert retrieve("E1", pair, kb) == [], "E1 pakai demo tetap, bukan retrieval"
    assert [c["id"] for c in retrieve("E2", pair, kb)] == ["m1"]
    assert [c["id"] for c in retrieve("E3", pair, kb)] == ["m1"]
    got = {c["label"] for c in retrieve("E4", pair, kb)}
    assert got == {"malicious", "benign"}, "E4 wajib contrastive, dapat: " + str(got)
    assert retrieve("E4", pair, []) == [], "KB kosong tidak boleh crash"

    assert parse_verdict('bla {"verdict":"benign"} bla')["verdict"] == "benign"
    assert parse_verdict("tanpa json") is None
    assert parse_verdict('{"rusak": }') is None
    print("ok")


if __name__ == "__main__":
    if "--selfcheck" in sys.argv:
        selfcheck()
    else:
        main()
