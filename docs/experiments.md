# Pelaksanaan eksperimen

**Cakupan aktif D99 (14 Oktober 2026):** lihat
[protokol eksperimen berbasis dataset](source-labelled-final-20261014.md).
Label sumber menggantikan kewajiban anotasi ganda; RQ2/RQ3 dilaporkan sebagai
perbandingan MAL+TYP. Hipotesis konfirmatori FPR_HN, minimum HN, κ dan gold
evidence di rancangan lama di bawah tidak diklaim terpenuhi oleh D99.

Revisi 2026-09-13. Seluruh prosedur ada di [methodology.md](methodology.md). File
ini hanya berisi jadwal, volume run, skema file, dan checklist implementasi.

**Syarat hasil paper, ditegaskan pengguna 12 Oktober 2026 (D91):** seluruh
kombinasi eksperimen yang diklaim harus benar-benar dijalankan pada cakupan
yang ditetapkan sebelum inferensi. Jumlah pair × model × konfigurasi × seed
harus dicocokkan dengan respons mentah unik dan log; invalid/kegagalan serta
kombinasi belum dijalankan tetap dilaporkan. Fixture, simulasi, proyeksi, dan
subset diagnostik tidak menggantikan evaluasi penuh. Kontrol historis harus
nyata, terverifikasi, sesuai protokol, dan tidak dihitung sebagai inferensi baru.
Kelengkapan panggilan tidak menggantikan gold, split data, atau card terverifikasi.

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
| Dev set | 10 pair × 6 konfigurasi × 2 model = 120 |
| Stage 1 | ~250 pair × 6 konfigurasi × 2 model = 3.000 |
| Stage 2 (EA2) | ~250 pair × 2 konfigurasi × 3 seed × 2 model = 3.000 |

Warm-up menambah 3 request per sesi server dan tidak dicatat.

## 3. Skema file

Dua berkas perantara memuat fakta yang tidak bisa diturunkan dari kode (D65):

**`data/wanted.jsonl`** — satu baris per versi yang perlu diunduh: `name`,
`version`, `origin` (`registry` atau `replication`), dan `tarball` kalau
sumbernya berkas lokal.

Pengumpulan memakai berkas kerja `data/typ.jsonl` (hasil undian TYP),
`data/pool.jsonl` (1.900 sisanya, kolam jalur A beserta urutan penggantinya), dan
`data/hn_candidates.jsonl` (hasil penyaringan jalur A). Ketiganya memberi isi
`wanted.jsonl` dan `pairs.manifest.jsonl`, bukan dibaca runner (D66).

**`data/pairs.manifest.jsonl`** — satu baris per pair: `before_dir`, `after_dir`,
dan metadata §3 yang berasal dari pengumpulan serta pelabelan (`subset`,
`category`, `campaign`, `source`, `published_at`, `label`, `gold_evidence`).
Pair berlabel `skip` dikeluarkan di sini dan jumlahnya dilaporkan (§8).

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

Status per 2026-09-28. Akuisisi data asli dan pemeriksaan sumber sudah berjalan;
[laporan data](real-data-20260928.md) memuat jumlah aktual dan eksklusi. Prompt,
runner, perakit, dan rekonstruksi normalisasi statis sudah tersedia. Batch data
asli selesai: 1.157 pair tanpa error pair, dengan 1.035 kandidat review
([laporan 29 September](preprocessing-20260929.md)). Verifikasi serta anotasi manusia, klaster final, dan card
KB belum selesai; G1/G2 belum tercapai.

**Prompt** — [pipeline/prompts.py](../pipeline/prompts.py)

- [x] Ganti `CONFIGS` menjadi `DIFF, DIFF+I, DIFF+I+M, DIFF+I+MM, DIFF+I+MB, DIFF+MB` (D62); hapus `E1` (D8), `E2` (D61), dan `FIXED_DEMO`.
- [x] Ganti `SYSTEM` dengan teks verbatim methodology §6.1 ([L10-L18](../pipeline/prompts.py#L10-L18)).
- [x] Ubah `_pair_block` sesuai template §6.2: hapus nama paket dan capability delta, tambah blok intent terstruktur ([L30-L38](../pipeline/prompts.py#L30-L38)).
- [x] Ubah `_card_block` sesuai §5.1: label `MALICIOUS`/`BENIGN`, dan delta tidak dicetak ([L41-L47](../pipeline/prompts.py#L41-L47)).
- [x] Taruh instruksi format JSON di akhir pesan user.

**Runner** — [pipeline/runner.py](../pipeline/runner.py)

- [x] Perbarui `retrieve` sesuai §5.2 ([L54-L66](../pipeline/runner.py#L54-L66)):
  - kecualikan card dengan paket atau kampanye yang sama;
  - pecah skor seri dengan hash;
  - tambah `DIFF+I+MM`;
  - counterbalance urutan card di `DIFF+I+MM`, `DIFF+I+MB`, dan `DIFF+MB`.
- [x] Ganti `parse_verdict` dengan `raw_decode` dan validasi §7 ([L69-L77](../pipeline/runner.py#L69-L77)).
- [x] `call_llm`: kirim temperature, top_p, dan top_k dari argumen, lalu kembalikan `finish_reason` ([L80-L101](../pipeline/runner.py#L80-L101)).
- [x] Masukkan temperature ke `run_key` ([L34-L35](../pipeline/runner.py#L34-L35)). Tanpa ini, run Stage 2 dengan seed 0 dianggap sudah selesai dan dilewati.
- [x] Simpan field hasil tambahan (§3).
- [x] Ganti default `--base-url` yang memakai port 8000 dan bentrok dengan backend ([L107](../pipeline/runner.py#L107)). Sekarang 8101; backend pindah ke 8100. Port 8000 dipakai production-service di mesin GPU.
- [x] Perbarui `selfcheck` untuk konfigurasi dan aturan baru ([L170-L201](../pipeline/runner.py#L170-L201)).

**Komponen baru**

- [x] Pengunduh dan ekstraksi sampel (§4.1) — [pipeline/samples.py](../pipeline/samples.py).
  Dua fase sesuai §4.1: `fetch` butuh jaringan dan tidak pernah membuka arsip,
  `extract` membuka arsip dan dijalankan tanpa jaringan. Checksum diverifikasi ulang
  sebelum arsip dibuka, anggota arsip yang keluar dari direktori target atau berupa
  link ditolak dan dilaporkan, dan awalan `package/` npm dibuang supaya `package.json`
  ada di akar direktori versi. Asal tiap tarball dicatat (D59).
- [x] Perakit `pairs.jsonl` (§3, §4.2–§4.5) — [pipeline/dataset.py](../pipeline/dataset.py).
  Merangkai smartdiff, intent, dan capability menjadi satu baris per pair: diff dipotong
  **sekali di sini**, bukan di runner; intent dari v_(t-1); delta beserta `delta_evidence`;
  checksum dijoin dari `samples.jsonl`; pair `skip` dikeluarkan dan dihitung; urutan
  keluaran mengikuti hash `name@versi` sehingga tidak bergantung urutan manifest.
- [x] Capability extractor (§4.3) — [pipeline/capability.py](../pipeline/capability.py). `--before/--after` untuk pair, `--single` untuk card malicious-intent, `--selfcheck` untuk aturan tabelnya. `--explain` melaporkan file, baris, dan potongan yang memicu tiap sinyal, untuk verifikasi kandidat HN (§3.3); simpan sebagai `delta_evidence` di `pairs.jsonl` supaya UI bisa menampilkannya. Definisi "file teks" pada `large_deletion` diambil sebagai "bisa didekode UTF-8", karena §4.3 tidak menyebutkannya.
- [~] Smart-diff dan pemotongan (§4.2, §4.5) — [pipeline/smartdiff.py](../pipeline/smartdiff.py).
  Langkah 3–7 dan seluruh §4.5 selesai: `diff -ruN`, file biner, pemotongan baris 2.000
  karakter, pembagian per file, prioritas (package.json → file bersinyal → sisanya),
  dan pemotongan pada batas hunk. Penghitung token di-inject; `qwen_counter()` memakai
  tokenizer §4.5 di mesin GPU, `--approx` untuk uji cepat.
  **Langkah 1–2 tersedia sebagai rekonstruksi statis lokal**
  `static-dolos-exact-v2` (D72–D76), karena `index.mjs` upstream tidak dirilis.
  Input mentah tidak diubah, literal berbeda dipertahankan, dan fallback dicatat.
  Dependensi alat dikunci di `deployments/preprocess/`. Raw diff audit lama tetap
  terpisah dari hasil preprocessing baru; rekonstruksi tidak diklaim identik Wyss.
- [x] Intent profile builder (§4.4) — [pipeline/intent.py](../pipeline/intent.py).
  Diambil dari v_(t-1) (D14), anggaran 1.024 token dengan README menyerap sisa yang
  tidak terpakai bagian lain, baris badge dan tag HTML dibuang, field kosong ditulis
  `not available`, dan `intent_available` mengikuti aturan description/README §4.4.
  Penghitung token di-inject seperti smartdiff. Lihat D51 soal pencocokan nama README.
- [~] Pengumpulan kandidat jalur B (§3.3) — [pipeline/collect.py](../pipeline/collect.py).
  `search --category N` mencari registry dengan kata kunci tetap, `pairs --package X`
  membangun pasangan rilis menurut D27. Aturan v_(t-1) diuji terhadap data axios asli:
  24 dari 144 versi mendapat v_(t-1) berbeda dibanding aturan waktu terbit, jadi D27
  bukan sekadar kehati-hatian. Langkah unduh tarball + ekstraksi sengaja TIDAK ada di
  sini: §4.1 mewajibkannya di container tanpa jaringan.
- [x] Pembagian HN menjadi subset uji dan kolam card benign (§3.3, D60) —
  [pipeline/hardnegative.py](../pipeline/hardnegative.py). Berstrata per kategori yang
  ditetapkan anotator, kuota card diisi lebih dulu supaya setiap kategori tetap punya
  pembanding benign, lalu kekurangan kuota uji diisi dari kategori surplus menurut
  urutan hash. Komposisi akhir per kategori dilaporkan, dan kandidat tanpa kategori
  dihitung, tidak ditebak (D68).
- [x] Pemilihan card malicious dan batas ukuran card (§3.4, §5.1) — [pipeline/kb.py](../pipeline/kb.py).
  `select` menjalankan round-robin atas 8 capability dalam urutan tabel, masing-masing
  menurut urutan hash, dengan maksimal 2 card per kampanye dan kampanye MAL test
  dilewati; keluarannya skeleton dengan empat field anotator dibiarkan kosong.
  `fit` menahan tiap card pada 15 baris excerpt lalu 512 token (D67).
- [x] Undian TYP (§3.2) dan jalur A (§3.3) — [pipeline/typical.py](../pipeline/typical.py).
  `sample` membagi kedua daftar Wyss menjadi 100 TYP (50 per daftar) dan kolam 1.900
  berurutan, sehingga aturan pengganti §3.2 terdefinisi; `screen` menjalankan kolam itu
  lewat extractor dan menyimpan update yang deltanya tidak kosong beserta
  `signal_categories`. Identitas pair dibaca dari `package.json`, bukan dari tata letak
  path yang belum diverifikasi (D66, D69). Sudah dijalankan atas data asli:
  100 TYP terpilih dan 182 kandidat HN dengan delta. Verifikasi tujuan sah dan
  kategori oleh anotator masih diperlukan.
- [~] Pengelompokan kampanye (§3.6) — [pipeline/campaign.py](../pipeline/campaign.py).
  Kriteria (a) laporan sama dan (b) file tambahan identik selesai dan teruji, dengan
  penutupan transitif dan pelaporan jumlah klaster pada ambang 0,5 dan 0,8. Label kampanye
  memakai id terkecil sehingga tidak bergantung urutan baca.
  **Kriteria (c) Dolos sudah dijalankan:** adapter JSON library 3.5.1 memakai
  k-gram 70/window 17. Gabungan 875 kandidat MAL dan 995 entri KB tersedia
  menghasilkan 714 klaster pada 0,5 dan 735 pada 0,8, tanpa error fingerprint.
  Ini masih mencakup prefix KB; pemetaan seluruh pool dan verifikasi insiden
  belum selesai (D75, [laporan](preprocessing-20260929.md)).
- [x] Skrip analisis (§11) — [pipeline/analysis.py](../pipeline/analysis.py).
  Metrik, kebijakan D18, aturan cocok evidence, flip rate, p95 nearest-rank, sel diskordan
  McNemar, bootstrap per kampanye (numpy, seed 2026), dan keempat label §5 selesai dan
  teruji. Wilson, McNemar exact, Holm, dan Cohen's kappa jadi wrapper tipis ke
  `statsmodels` sesuai D43. `statsmodels` dan `matplotlib` sudah terpasang di mesin
  RTX 5090; selfcheck analisis dan [plot](../pipeline/plots.py) lulus pada 2026-09-28,
  bersama 13 selfcheck pipeline lainnya. Evaluasi dataset sungguhan belum dilakukan.

**Smoke test model, 2026-09-28:** Qwen2.5-Coder-3B menjalankan 3 warm-up dan
24 panggilan fixture secara sekuensial; 24/24 respons valid, tanpa error transport.
Retrieval dan resume terverifikasi. Artefak berada di `scratchpad/20260928-qwen25-smoke/`,
terpisah dari `data/results.jsonl`. [Laporan lengkap](smoke-20260928.md) mencatat
perbaikan startup, setelan, biaya inferensi, dan keterbatasannya. Gate G2 belum dipenuhi.

**Data dan UI**

- [x] Arsip OSF dan snapshot Datadog diperoleh; 100 TYP, 182 kandidat HN,
  45 pair audit Wyss, dan 830 kandidat Datadog tersedia. Manifest pemeriksaan
  ada di `data/acquisition/`. Ini belum dataset final berlabel ganda.
- [ ] Verifikasi manusia, anotasi independen, klaster gabungan, card KB, dan
  pemilihan dev/test set final.

- [x] Tambah field skema pair (§3) ke tipe `Pair` di [frontend/src/types/api.ts](../frontend/src/types/api.ts#L10-L20), plus filter per `subset` dan `category`. Kategori HN juga bisa dilabeli di UI (§8).
- [x] Dukung label ganda. Satu file per anotator: `data/audit_decisions.<anotator>.json`. UI menahan di gerbang identitas, dan `GET /api/annotators` hanya melaporkan jumlah, bukan label.
- [x] Taksonomi error capability/intent/retrieval sudah ada di UI dan sesuai dengan EA4.
