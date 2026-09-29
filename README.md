# IntentDiff-RAG

Tugas Metodologi Penelitian, S2 ITS: Robby Ulung Pambudi (6025252022) dan
Gloriyano Cristho Daniel Pepuho (6025252017).

**Pertanyaan besarnya:** bisakah LLM open-weight 3–4B yang jalan lokal
membedakan update npm yang berbahaya dari update sah yang perilakunya mirip?

> Ini eksperimen penelitian, bukan production scanner. Sampel malicious hanya
> dianalisis statis: tidak pernah di-`npm install`, dieksekusi, atau dijalankan
> lifecycle script-nya.

## Masalah

Update pada paket yang sudah dipercaya bisa menyisipkan payload, contohnya
chalk/debug dan worm Shai-Hulud (September 2025) serta axios (Maret 2026).
`npm audit` tidak menangkap serangan seperti ini karena hanya mencocokkan
advisory yang sudah terbit. Wyss et al. (RAID 2025) menunjukkan LLM tertutup
bisa mendeteksinya dengan akurat dari smart-diff. Yang belum diketahui: apakah
model kecil yang bisa jalan lokal juga mampu, dan apakah false positive pada
perilaku sensitif yang sah (telemetry, install hook, validasi lisensi) bisa
ditekan dengan contoh pembanding benign dan intent paket.

Posisi penelitian ini: **triage update dependensi sebelum advisory terbit**,
pelengkap `npm audit`, bukan audit tata kelola TI.

## Pertanyaan penelitian (revisi 2026-09-13)

| | Pertanyaan | Jenis | Pembanding |
|---|---|---|---|
| RQ1 | Seberapa akurat model 3–4B mendeteksi update berbahaya dari smart-diff tanpa contoh, diukur dari recall dan FPR? | Deskriptif | DIFF, DIFF+I |
| RQ2a | Apakah contoh malicious hasil retrieval menaikkan FPR pada hard negative? | Uji hipotesis | DIFF+I+M vs DIFF+I |
| RQ2b | Dengan jumlah contoh yang sama, apakah benign look-alike menurunkan FPR hard negative tanpa recall turun lebih dari 5 poin? | Uji hipotesis (utama) | DIFF+I+MB vs DIFF+I+MM |
| RQ3 | Apakah intent paket eksplisit menurunkan FPR hard negative tanpa recall turun lebih dari 5 poin? | Uji hipotesis | DIFF+I+MB vs DIFF+MB |
| RQ4 | Berapa tambahan token, latency, dan memori GPU dari tiap komponen? | Deskriptif | semua konfigurasi |

Hipotesis, decision rule, dan ancaman validitas ada di
[docs/research.md](docs/research.md). RQ di proposal P1 (slide 10) sudah
tidak berlaku; alasan tiap perubahan ada di [docs/decisions.md](docs/decisions.md).

## Status

- [x] Proposal P1 — `labs/refrences/P1_Metodologi Penelitian.pdf`
- [x] Audit referensi ke sumber asli — [docs/references.md](docs/references.md)
- [x] Revisi RQ, hipotesis, dan protokol eksperimen
- [x] Metodologi final — [docs/methodology.md](docs/methodology.md)
- [x] Kerangka runner, prompt builder, dan UI label audit
- [x] Penyesuaian kode ke konfigurasi revisi (D62) — [checklist](docs/experiments.md#4-checklist-implementasi)
- [x] Pengunduh, ekstraksi statis, intent profile, capability extractor,
      dan perakit `pairs.jsonl`; kekurangan smart-diff dicatat di bawah
- [x] Seluruh aturan pemilihan dalam kode: undian TYP dan jalur A, pembagian hard
      negative, pemilihan card malicious, dan batas ukuran card
- [x] Akuisisi data asli: 100 TYP, 182 kandidat HN, 45 pair audit Wyss,
      dan 830 kandidat pair Datadog — [laporan](docs/real-data-20260928.md)
- [ ] Dataset final: verifikasi manusia, klaster gabungan, pembagian test/KB,
      anotasi independen, dan card KB belum selesai
- [x] `statsmodels` dan `matplotlib` terpasang; 21 pemeriksaan pipeline lulus
- [x] Smoke test Qwen2.5-Coder-3B pada RTX 5090: 3 warm-up + 24 panggilan
      fixture, 24/24 JSON valid — [laporan](docs/smoke-20260928.md).
      Ini belum merupakan evaluasi dev/test set.
- [x] Dolos kampanye selesai untuk 1.870 item tersedia: 714 klaster pada
      ambang 0,5 dan 735 pada 0,8; cakupan KB masih prefix
- [x] Normalisasi statis lokal `static-dolos-exact-v2` tersedia dan diuji;
      rekonstruksi karena `index.mjs` upstream tidak dirilis (D72–D76)
- [x] Preprocessing 1.157 pair selesai; 1.035 kandidat siap anotasi —
      [laporan](docs/preprocessing-20260929.md), UI http://127.0.0.1:5174/
- [x] Pool KB penuh: 24.324 arsip terverifikasi, 24.198 identitas valid;
      clustering gabungan 25.073 item selesai (3.681/4.114 klaster pada 0,5/0,8)
- [x] Bobot Qwen3-4B tersedia lokal; seluruh prompt baseline kandidat muat
      pada tokenizer kedua model, tanpa inferensi baru
- [~] Baseline eksploratif data asli berjalan: 973 pair × 2 konfigurasi ×
      2 model; label sumber, terpisah dari studi konfirmatori (D81).
      [Protokol run](data/evaluation/source-baselines-20260929/protocol.json)
- [ ] Inferensi test set konfirmatori menunggu dataset final dan anotasi —
      [panduan review data asli](docs/annotation-20260928.md)

## Peta dokumen

| File | Isi |
|---|---|
| [docs/research.md](docs/research.md) | masalah, posisi terhadap penelitian terkait, gap, RQ, hipotesis, decision rule, ancaman validitas |
| [docs/methodology.md](docs/methodology.md) | prosedur final: data, smart-diff, capability extractor, intent profile, KB dan retrieval, prompt verbatim, inferensi, metrik, statistik |
| [docs/experiments.md](docs/experiments.md) | pelaksanaan: timeline dan gate, volume run, skema file, checklist implementasi |
| [docs/references.md](docs/references.md) | status tiap referensi, fakta yang boleh dikutip, koreksi slide P1, referensi yang perlu ditambah |
| [docs/decisions.md](docs/decisions.md) | log keputusan bertanggal beserta alasannya |
| [.agent/](.agent/) | ringkasan operasional untuk agent AI: invarian kode, skema file, urutan run, posisi terhadap RogueOne. `docs/` tetap sumber kebenaran |
| `labs/latex/` | naskah (Elsevier CAS) |
| [CLAUDE.md](CLAUDE.md) | aturan kerja untuk Claude Code |

## Menjalankan

```bash
# backend: API untuk UI audit
cd backend && cargo run -- --data-dir ../data --port 8100
cargo test

# frontend: http://localhost:5174, mem-proxy /api ke port 8100
cd frontend && pnpm install && pnpm dev
pnpm test

# pipeline: butuh server vLLM (D46 — Ollama hanya untuk smoke test mekanik)
python pipeline/runner.py --model Qwen/Qwen3-4B-Instruct-2507 --base-url http://localhost:<port-model>
python pipeline/runner.py --selfcheck
```

Backend memakai 8100 dan vLLM 8101; runner sudah default ke 8101. Port 8000
sengaja dihindari karena di mesin GPU sudah dipakai production-service, bersama
8080, 8081, 5433, 9400, dan 18888. Jalankan `docker ps` sebelum mengubahnya.
