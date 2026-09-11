# IntentDiff-RAG

Riset: *Detecting Malicious npm Updates with Small Open-Weight LLMs* (ITS).

**Ini eksperimen penelitian, bukan production scanner.** Nilai setiap keputusan
teknis dari "apakah ini menjawab RQ", bukan dari kelengkapan fitur.

## Aturan

- **Sampel malicious hanya dianalisis statis.** Jangan pernah dieksekusi, di-`npm install`, atau dijalankan lifecycle script-nya. Tidak ada network call ke endpoint yang muncul di dalam sampel.
- **`.ref/` read-only** — bahan referensi, bukan kode proyek. Jangan diedit.
- **Laporkan angka apa adanya.** Kalau satu konfigurasi kalah dari baseline, itu hasil — bukan bug yang harus di-tuning sampai menang.
- Scope 8 minggu. Di luar scope kecuali diminta: web UI, CI integration, service/API, dynamic sandbox execution, fine-tuning, model tertutup.

## Konteks

`frontend/` — alat kerja riset: label audit (M1-2) dan error analysis (M7-8).
Vite + React + TS + Tailwind. Konvensi struktur mengikuti `.ref/spider/frontend`,
bahasa desain (token warna, komponen flat) mengikuti `.ref/cloudx_ui`.

```
cd frontend && pnpm install
pnpm dev           # http://localhost:5174 (butuh backend jalan)
pnpm test          # logika filter + agregasi
pnpm build         # tsc --noEmit && vite build
```

`pipeline/` — runner eksperimen. Batch, bukan service: baca pairs, jalankan
E0-E4 lewat endpoint OpenAI-compatible (vLLM/Ollama), tulis satu baris per run.

```
python pipeline/runner.py --model Qwen/Qwen3-4B-Instruct-2507
python pipeline/runner.py --selfcheck
```

Resumable — run yang sudah ada di `results.jsonl` dilewati, jadi batch boleh
dihentikan kapan saja. Sekuensial dengan sengaja: RQ3 mengukur median dan p95
latency, dan angka itu rusak kalau request tumpang tindih di server.

Peak VRAM tidak diukur runner (satu angka per model yang dimuat, bukan per
request) — catat terpisah lewat nvidia-smi.

`backend/` — API untuk UI audit. Rust + axum.

```
cd backend && cargo run -- --data-dir ../data --port 8000
cargo test
```

Data dibaca dari `data/pairs.jsonl` (fallback `data/pairs.sample.jsonl`; KB di
`data/kb.jsonl`), keputusan ditulis ke `data/audit_decisions.json` — dataset
input tidak pernah disentuh. Menyajikan file, bukan database: runner Python dan
backend membaca-menulis file yang sama.

Tulis keputusan dijaga mutex dan lewat rename atomik, jadi dua klik berdekatan
tidak saling menimpa dan proses yang mati saat menulis tidak merusak file.

Frontend mem-proxy `/api` ke port 8000, jadi backend harus jalan lebih dulu.

- `.agent/research.md` — RQ, hipotesis, pipeline, decision rule, gap
- `.agent/experiments.md` — matriks E0–E4, data, metrik, timeline
- `.agent/rogueone.md` — posisi terhadap RogueOne, novelty yang diambil & di-skip
- `.ref/P1_Metodologi Penelitian.pdf` — proposal, sumber kebenaran untuk scope
- `.ref/rogueone/` — kode RogueOne (ICSE 2024), baseline
