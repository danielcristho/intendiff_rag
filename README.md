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
| RQ1 | Seberapa akurat model 3–4B mendeteksi update berbahaya dari smart-diff tanpa contoh, diukur dari recall dan FPR? | Deskriptif | E0-noint, E0 |
| RQ2a | Apakah contoh malicious hasil retrieval menaikkan FPR pada hard negative? | Uji hipotesis | E3 vs E0 |
| RQ2b | Dengan jumlah contoh yang sama, apakah benign look-alike menurunkan FPR hard negative tanpa recall turun lebih dari 5 poin? | Uji hipotesis (utama) | E4 vs E3-k2 |
| RQ3 | Apakah intent paket eksplisit menurunkan FPR hard negative tanpa recall turun lebih dari 5 poin? | Uji hipotesis | E4 vs E4-noint |
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
- [ ] Dataset (`data/` belum ada)
- [ ] Smart-diff, intent profile, capability extractor, skrip analisis
- [ ] Penyesuaian kode ke konfigurasi revisi — [checklist](docs/experiments.md#4-checklist-implementasi)

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

## Menjalankan

```bash
# backend: API untuk UI audit; JWT_SECRET dibaca dari .env
make user-add NAME=daniel      # buat akun anotator (password diminta di terminal)
make backend
cd backend && cargo test

# frontend: http://localhost:5174, mem-proxy /api ke port 8100
cd frontend && pnpm install && pnpm dev
pnpm test

# pipeline: butuh server vLLM (D46 — Ollama hanya untuk smoke test mekanik)
python -m pipeline run --model Qwen/Qwen3-4B-Instruct-2507   # URL dari VLLM_PORT di .env
python -m pipeline selfcheck
```

Backend memakai 8100 dan vLLM 8101; runner sudah default ke 8101. Port 8000
sengaja dihindari karena di mesin GPU sudah dipakai production-service, bersama
8080, 8081, 5433, 9400, dan 18888. Jalankan `docker ps` sebelum mengubahnya.
