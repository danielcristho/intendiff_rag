# IntentDiff-RAG

Riset: *Detecting Malicious npm Updates with Small Open-Weight LLMs* (ITS).

**Ini eksperimen penelitian, bukan production scanner.** Nilai setiap keputusan
teknis dari "apakah ini menjawab RQ", bukan dari kelengkapan fitur.

## Aturan

- **Sampel malicious hanya dianalisis statis.** Jangan pernah dieksekusi, di-`npm install`, atau dijalankan lifecycle script-nya. Tidak ada network call ke endpoint yang muncul di dalam sampel.
- **`.ref/` read-only** — bahan referensi, bukan kode proyek. Jangan diedit.
- **Laporkan angka apa adanya.** Kalau satu konfigurasi kalah dari baseline, itu hasil — bukan bug yang harus di-tuning sampai menang.
- **Desain yang berlaku ada di `docs/`, bukan di slide P1.** RQ proposal sudah direvisi (2026-09-13). Setiap perubahan desain dicatat di `docs/decisions.md`.
- **Desain dibekukan di Gate G2** (akhir M4). Setelah itu, perubahan prompt, konfigurasi, daftar capability, atau decision rule wajib dicatat di `docs/decisions.md` dan semua konfigurasi dijalankan ulang. Jangan menyetel prompt berdasarkan hasil test set.
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
setiap konfigurasi lewat endpoint OpenAI-compatible (vLLM/Ollama), tulis satu
baris per run. Kode masih memakai E0–E4 lama; konfigurasi revisi dan checklist
penyesuaiannya ada di `docs/methodology.md` dan `docs/experiments.md` §4.

```
python pipeline/runner.py --model Qwen/Qwen3-4B-Instruct-2507
python pipeline/runner.py --selfcheck
```

Resumable — run yang sudah ada di `results.jsonl` dilewati, jadi batch boleh
dihentikan kapan saja. Sekuensial dengan sengaja: RQ4 mengukur median dan p95
latency, dan angka itu rusak kalau request tumpang tindih di server.

Memori GPU tidak diukur runner. Jangan pakai puncak nvidia-smi sebagai metrik:
vLLM mempra-alokasi memori sesuai `--gpu-memory-utilization`. Cara ukurnya ada
di `docs/methodology.md` §9.3 (D41).

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
Default `--base-url` runner juga port 8000 — jangan jalankan server model di
port yang sama dengan backend.

- `docs/research.md` — masalah, posisi, gap, RQ1–RQ4, hipotesis, decision rule, ancaman validitas
- `docs/methodology.md` — prosedur final: data, smart-diff, extractor, intent, KB & retrieval, prompt verbatim, inferensi, metrik, statistik
- `docs/experiments.md` — pelaksanaan: timeline & gate, volume run, skema file, checklist implementasi
- `docs/references.md` — status referensi (dicek ke sumber asli), fakta yang boleh dikutip, koreksi slide P1
- `docs/decisions.md` — log keputusan bertanggal; tambahkan entri setiap desain berubah
- `labs/refrences/P1_Metodologi Penelitian.pdf` — proposal awal; scope masih berlaku, RQ-nya sudah digantikan `docs/research.md`
- `.agent/research.md` — ringkasan untuk agent: RQ → konfigurasi, invarian yang tidak boleh dilanggar, larangan, istilah
- `.agent/experiments.md` — spesifikasi konfigurasi untuk kode, skema file, urutan run, penanganan sampel yang aman
- `.agent/rogueone.md` — posisi terhadap RogueOne: ide yang diambil & di-skip, angka yang boleh dikutip (tidak dijalankan ulang, D20)

`docs/` adalah sumber kebenaran; `.agent/` adalah ringkasan operasionalnya. Kalau
keduanya berbeda, `docs/` yang benar dan `.agent/` diperbarui.
