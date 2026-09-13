# Pelaksanaan eksperimen

Revisi 2026-09-13. Seluruh prosedur ada di [methodology.md](methodology.md). File
ini hanya berisi jadwal, volume run, skema file, dan checklist implementasi.

## 1. Timeline dan gate

| Minggu | Pekerjaan | Keluaran | Gate |
|---|---|---|---|
| M1–2 | Unduh paket replikasi Wyss (OSF) dan dataset Datadog; bangun capability extractor (§4.3), karena jalur A HN membutuhkannya; kumpulkan MAL, TYP, HN, dan pool KB; bentuk klaster kampanye; label ganda; hitung κ | `data/pairs.jsonl` berlabel, pool KB, nilai κ | **G1:** jumlah per subset dibandingkan dengan minimum untuk menentukan RQ mana yang diuji inferensial. Catat di decisions.md |
| M3–4 | Smart-diff dan pemotongan, intent profile, card KB, retrieval, prompt baru, parser, skrip analisis (diuji dengan data dummy); jalankan dev set | smoke test dev set, validitas JSON | **G2:** revisi format diputuskan (§6.4), lalu seluruh desain dibekukan |
| M5–6 | Warm-up, Stage 1, Stage 2, pencatatan memori | `data/results.jsonl` | — |
| M7–8 | Analisis sesuai §11; EA1–EA5 (error analysis di UI audit); penulisan | tabel dan naskah | — |

## 2. Volume run

| Run | Jumlah panggilan |
|---|---|
| Dev set | 10 pair × 7 konfigurasi × 2 model = 140 |
| Stage 1 | ~250 pair × 7 konfigurasi × 2 model = 3.500 |
| Stage 2 (EA2) | ~250 pair × 2 konfigurasi × 3 seed × 2 model = 3.000 |

Warm-up menambah 3 request per sesi server dan tidak dicatat.

## 3. Skema file

**`data/pairs.jsonl`** — satu baris per pair.

| Field | Isi |
|---|---|
| `id`, `name`, `before`, `after` | identitas pair; `name` tidak ditampilkan ke model |
| `subset`, `category` | `MAL`/`HN`/`TYP`; kategori HN 1–5 |
| `campaign`, `source`, `published_at` | klaster (§3.6), asal data, tanggal terbit v_t |
| `sha256_before`, `sha256_after` | checksum tarball |
| `intent` | objek `{description, keywords, scripts, readme}` dari v_{t−1} |
| `intent_available`, `intent_from` | §4.4 |
| `delta` | capability delta (§4.3) |
| `diff`, `truncated` | smart-diff setelah pemotongan (§4.5) |
| `label`, `gold_evidence` | label gold; baris malicious (MAL saja) |

**`data/kb.jsonl`** — satu baris per card: `id`, `label`, `campaign`, `source`,
`delta`, `intent`, `behavior_chain`, `code_excerpt`, `rationale` (§5.1).

**`data/results.jsonl`** — field yang sudah ada di runner, ditambah:

- `temperature`, `top_p`, `top_k`;
- `finish_reason`;
- `cards` (daftar `{id, label, score, position}`);
- `truncated`.

`run_key` harus memuat temperature.

## 4. Checklist implementasi

Status per 2026-09-13. Prompt dan runner sudah mengikuti desain revisi; komponen pra-pemrosesan dan skrip analisis belum.

**Prompt** — [pipeline/prompts.py](../pipeline/prompts.py)

- [x] Ganti `CONFIGS` menjadi `E0-noint, E0, E2, E3, E3-k2, E4, E4-noint`; hapus `E1` dan `FIXED_DEMO` ([L8](../pipeline/prompts.py#L8), [L22-L27](../pipeline/prompts.py#L22-L27)).
- [x] Ganti `SYSTEM` dengan teks verbatim methodology §6.1 ([L10-L18](../pipeline/prompts.py#L10-L18)).
- [x] Ubah `_pair_block` sesuai template §6.2: hapus nama paket dan capability delta, tambah blok intent terstruktur ([L30-L38](../pipeline/prompts.py#L30-L38)).
- [x] Ubah `_card_block` sesuai §5.1: label `MALICIOUS`/`BENIGN`, dan delta tidak dicetak ([L41-L47](../pipeline/prompts.py#L41-L47)).
- [x] Taruh instruksi format JSON di akhir pesan user.

**Runner** — [pipeline/runner.py](../pipeline/runner.py)

- [x] Perbarui `retrieve` sesuai §5.2 ([L54-L66](../pipeline/runner.py#L54-L66)):
  - kecualikan card dengan paket atau kampanye yang sama;
  - pecah skor seri dengan hash;
  - tambah `E3-k2`;
  - counterbalance urutan card di `E3-k2` dan `E4`.
- [x] Ganti `parse_verdict` dengan `raw_decode` dan validasi §7 ([L69-L77](../pipeline/runner.py#L69-L77)).
- [x] `call_llm`: kirim temperature, top_p, dan top_k dari argumen, lalu kembalikan `finish_reason` ([L80-L101](../pipeline/runner.py#L80-L101)).
- [x] Masukkan temperature ke `run_key` ([L34-L35](../pipeline/runner.py#L34-L35)). Tanpa ini, run Stage 2 dengan seed 0 dianggap sudah selesai dan dilewati.
- [x] Simpan field hasil tambahan (§3).
- [x] Ganti default `--base-url` yang memakai port 8000 dan bentrok dengan backend ([L107](../pipeline/runner.py#L107)). Sekarang 8101; backend pindah ke 8100. Port 8000 dipakai production-service di mesin GPU.
- [x] Perbarui `selfcheck` untuk konfigurasi dan aturan baru ([L170-L201](../pipeline/runner.py#L170-L201)).

**Komponen baru**

- [x] Capability extractor (§4.3) — [pipeline/capability.py](../pipeline/capability.py). `--before/--after` untuk pair, `--single` untuk card malicious-intent, `--selfcheck` untuk aturan tabelnya. `--explain` melaporkan file, baris, dan potongan yang memicu tiap sinyal, untuk verifikasi kandidat HN (§3.3); simpan sebagai `delta_evidence` di `pairs.jsonl` supaya UI bisa menampilkannya. Definisi "file teks" pada `large_deletion` diambil sebagai "bisa didekode UTF-8", karena §4.3 tidak menyebutkannya.
- [ ] Smart-diff dan pemotongan (§4.2, §4.5), dijalankan di container tanpa jaringan.
- [ ] Intent profile builder (§4.4).
- [~] Pengumpulan kandidat jalur B (§3.3) — [pipeline/collect.py](../pipeline/collect.py).
  `search --category N` mencari registry dengan kata kunci tetap, `pairs --package X`
  membangun pasangan rilis menurut D27. Aturan v_(t-1) diuji terhadap data axios asli:
  24 dari 144 versi mendapat v_(t-1) berbeda dibanding aturan waktu terbit, jadi D27
  bukan sekadar kehati-hatian. Langkah unduh tarball + ekstraksi sengaja TIDAK ada di
  sini: §4.1 mewajibkannya di container tanpa jaringan.
- [ ] Jalur A (§3.3): jalankan 1.900 typical update sisa Wyss lewat extractor. Menunggu unduhan OSF.
- [ ] Pengelompokan kampanye (§3.6).
- [ ] Skrip analisis (§11).

**Data dan UI**

- [x] Tambah field skema pair (§3) ke tipe `Pair` di [frontend/src/types/api.ts](../frontend/src/types/api.ts#L10-L20), plus filter per `subset` dan `category`. Kategori HN juga bisa dilabeli di UI (§8).
- [x] Dukung label ganda. Satu file per anotator: `data/audit_decisions.<anotator>.json`. UI menahan di gerbang identitas, dan `GET /api/annotators` hanya melaporkan jumlah, bukan label.
- [x] Taksonomi error capability/intent/retrieval sudah ada di UI dan sesuai dengan EA4.
