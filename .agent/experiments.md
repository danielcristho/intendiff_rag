# Ringkasan eksperimen untuk agent

**D85 selesai dan terverifikasi (1 Oktober 2026, 21:42 UTC+7): 160/160
inferensi nyata pada 32 kandidat HN dev, Qwen3-4B.** CUDA pulih setelah
restart WSL yang disetujui pengguna; startup gagal awal tetap disimpan.
Baca `docs/evidence-dev-results-20261001.md`. LEGACY-I: JSON valid 29/32,
alarm 5; SCHEMA-I: 32/32, alarm 6; IDS-I, IDS-D, VERIFY-I: semua 32/32,
alarm 0. Verifier tidak mengubah verdict dan metode dua tahap memakai
2,05 kali token IDS-I. Semua ID ditemukan, tetapi 27/96 respons format ID
mengutip header/hunk dan klaim semantik masih perlu verifikasi manusia.
Jangan menyebut nol alarm sebagai FPR 0%: tanpa gold dan cohort MAL dev,
recall/FPR belum diukur. Semua 160 HTTP 200, token/hash request cocok,
14 hash sumber, dua upstream, 13 model cocok. Server berhenti. Jangan
mengulang atau mengubah snapshot lengkap. `dev-exclusions.jsonl` wajib
diperhitungkan saat menyusun test/KB, termasuk klon setelah clustering HN.
Gold/card serta G1/G2 belum selesai. Delapan test bukti/prompt dan tiga
test launcher sudah lulus; tidak ada perubahan prompt saat batch berjalan.

**Sumber kebenaran:**

- [docs/methodology.md](../docs/methodology.md) untuk prosedur.
- [docs/experiments.md](../docs/experiments.md) untuk jadwal, skema file, dan checklist.

File ini menerjemahkan keduanya ke spesifikasi yang bisa langsung dipakai saat
menulis kode. Kalau isinya berbeda, yang benar `docs/`, dan file ini yang harus
diperbarui.

**D84 selesai dan terverifikasi (1 Oktober 2026, 09:24 WIB):** pengguna meminta eksplorasi model
lain. Phi-4-mini-instruct (3,836B) dan Llama-3.1-8B-Instruct (8,030B) dipilih
melalui audit akses/tokenizer, sebelum prediksi. Input/prompt/parser sama
dengan D83, BF16, output 2.048, server 32K. Startup Phi pertama gagal
pada alokasi buffer KV otomatis 15,80 GiB sebelum prediksi; kedua model
kini memakai KV eksplisit 6 GiB (menggantikan kalkulasi dari flag GPU 0,80).
Snapshot awal dan log kegagalan tersimpan; lihat `cache-amendment.json`.
Native
end-of-turn token IDs dari generation_config resmi diberikan pada request;
jangan menghapusnya karena mengubah penghentian giliran. Semua 973 pair ×
DIFF/DIFF+I: 3.892 inferensi baru, ditambah 7.784 kontrol D82/D83.
Direktori `data/evaluation/model-families-20261001/`: periksa
`download_status.json` dan `status.json` sebelum membuat proses baru.
Urutan acquire → freeze → evaluate. `probe.py` hanya audit tokenisasi
kandidat tanpa generasi. Mistral/DeepSeek tidak muat untuk sebagian prompt;
Granite cadangan membutuhkan konteks lebih besar. Bukan kandidat gagal
akurasi. Tidak ada pemotongan khusus model. Detail: `docs/model-families-20261001.md`.
Seluruh 3.892 respons unik lengkap, tanpa retry request atau error transport;
kedua server berhenti normal. `verify_final.py` memeriksa 30 hash aktif,
13 kontrol, dan 27 sumber arsip awal, token aktual, native stop IDs, serta
1.946 HTTP 200 per model. Phi DIFF/DIFF+I: recall sumber 45,93%/50,29%,
FPR 13%/13%, JSON valid 58,17%/82,94%; Llama: 85,45%/89,23%, FPR
57%/69%, JSON valid 88,08%/89,62%. Total invalid 790, terpotong 219.
Perbandingan lengkap mencakup 11.676 respons enam model. Jangan menjalankan
ulang untuk memperbaiki angka atau mengubah snapshot. Kegagalan startup
awal terjadi sebelum generasi, bukan prediksi yang dibuang. Perbaikan
format berikutnya perlu eksperimen/dev set tersendiri; G1/G2 tetap terbuka.

**D83 selesai dan terverifikasi (1 Oktober 2026):** pengguna menyetujui dua
pembanding prioritas dari `docs/model-scale-proposal-20260930.md`:
Qwen2.5-Coder-7B-Instruct dan Qwen3-8B non-thinking. Akuisisi, snapshot,
dan controller ada di `data/evaluation/model-scale-20260930/`.
Periksa `download_status.json` dan, setelah inferensi dimulai, `status.json`
sebelum melanjutkan; jangan menggandakan proses unduhan/evaluasi.
Urutan: `acquire.py`, `freeze.py` (audit token lokal dan checksum), lalu
`evaluate.py` (preflight, verifikasi template server tanpa generasi, seluruh
3.892 inferensi, ringkasan, perbandingan). Semua 973 pair memakai DIFF dan
DIFF+I, BF16, output 2.048, konteks 32.768, alokasi GPU 0,80.
Kontrol historis D82 tetap 3.892 respons pada output 2.048 dan alokasi 0,65.
Seluruh 3.892 respons baru unik selesai 1 Oktober 00:04 WIB, tanpa retry
atau error transport; `scratchpad/model-scale-20260930/verify_final.py`
lulus. 22 hash snapshot dan 13 hash kontrol cocok; 1.946 request HTTP 200
per model; server berhenti normal. Jangan mengulang inferensi yang sudah
lengkap atau mengubah snapshot. Qwen2.5-7B DIFF/DIFF+I: recall sumber
92,90%/67,12%, FPR 65%/67%; Qwen3-8B: 50,74%/48,34%, FPR 6%/3%.
Qwen2.5 DIFF menaikkan recall sekaligus FPR; Qwen3 lebih valid JSON-nya
tetapi recall turun dibanding kontrol 4B. Semua model memakai dua konfigurasi.
Hasil dan diagnosis: `docs/model-scale-20260930.md`; grafik, CSV, raw,
dan `verification.json` berada di direktori run. Tetap eksploratif;
G1/G2, gold manusia, HN, dan retrieval belum diselesaikan oleh eksperimen ini.

**Status kode (2026-09-25):** runner dan prompt builder sudah mengikuti desain revisi.
ID konfigurasi memakai skema semantik D62; skema lama `E0`–`E4` sudah tidak dipakai.
Sisa pekerjaan ada di `docs/experiments.md` §4.

**Data asli (2026-09-28):** akuisisi tersedia di `data/acquisition/` dan dirinci
di [laporan](../docs/real-data-20260928.md). Ada 100 TYP, 182 kandidat HN,
45 pair audit Wyss, dan 830 kandidat Datadog dengan pendahulu tersedia serta
tanpa advisory. **Pembaruan 29 September:** semua 1.157 pair selesai memakai
`static-dolos-exact-v2`; 1.035 kandidat terbit ke `data/review/pairs.jsonl`,
UI lokal port 5174. Ada 372 diff terpotong dan 332 pair dengan fallback.
Clustering 1.870 item tersedia selesai (714/735 klaster pada 0,5/0,8).
Label MAL/HN masih pending. Jangan memakai `*.audit.jsonl` mentah untuk
inferensi, menyamakan prefix KB 1.000 arsip dengan pool lengkap, atau label
sumber dengan anotasi manusia. `data/results.jsonl` belum ada; G1/G2 belum
selesai. Detail: [laporan preprocessing](../docs/preprocessing-20260929.md).

**Kelanjutan pool penuh:** 24.324 arsip KB sudah diunduh dan checksum ganda
diverifikasi; 24.198 identitas valid, 126 dikeluarkan. Proses otomatis
`scratchpad/full-kb-20260929/complete_pipeline.py` menjalankan material dan
clustering 25.073 item, kemudian memperbarui review jika tidak ada kegagalan.
Periksa `data/acquisition/full-kb-pipeline-state.json` dan log tahap sebelum
melanjutkan; jangan memulai pekerjaan yang sama dua kali. `combined-campaigns-complete.json`
tetap hasil prefix; keluaran penuh bernama `combined-campaigns-full.json`.
Bobot Qwen3-4B tersedia lokal pada revisi `cdbee75f17c01a7cc42f958dc650907174af0554`;
1.157 prompt DIFF+I sudah diperiksa dengan kedua tokenizer, seluruhnya muat.

**Evaluasi eksploratif disetujui pengguna (D81):** setelah diberi tahu syarat
anotasi, pengguna meminta evaluasi untuk memperoleh hasil dan mengonfirmasi
“boleh lanjutkan”. `data/evaluation/source-baselines-20260929/evaluate.py`
menjalankan 973 pair (873 MAL berlabel sumber + 100 TYP), DIFF/DIFF+I,
dua model bergantian pada RTX 5090, total 3.892 run. Tidak ada HN atau card
buatan. Snapshot masukan/prompt dibekukan dalam direktori tersebut; jangan
mengubahnya berdasarkan hasil. Periksa `status.json` dan `evaluation.log`
sebelum menjalankan ulang; evaluator melewati run sukses yang sudah selesai.
`summarize.py` memeriksa respons serta menyajikan metrik eksploratif, termasuk
invalid-as-benign/sensitivity dan macro recall per klaster. File hasil tidak
boleh dipromosikan menjadi hasil konfirmatori §8. Clustering penuh telah
selesai (3.681/4.114 klaster), dan paket review sudah memakai pemetaan penuh.

**Hasil D81 selesai, 29 September 2026:** 3.892 run unik lengkap; masing-masing
model mencatat 1.946 request HTTP 200, tanpa error transport tercatat atau
pengulangan run.
`verification.json` memeriksa kelengkapan, identitas pair, parameter, token,
metrik, CSV, dan konsistensi hasil dengan log server. Qwen2.5 DIFF/DIFF+I:
recall sumber 80,64%/68,16%, FPR TYP 45%/43%; Qwen3 DIFF/DIFF+I:
47,88%/56,70% dan 6%/3%. Output invalid dihitung benign sesuai D18;
1.077 dari 3.892 respons invalid. Semua angka tetap eksploratif, tanpa gold
manusia atau evaluasi retrieval. Laporan akhir: `report.md` di direktori run.
Server evaluasi telah dihentikan oleh controller. Jangan menjalankan ulang
untuk memperbaiki angka atau mengganti snapshot masukan/prompt.

**Audit Qwen2.5:** `docs/qwen25-audit-20260929.md` dan
`data/evaluation/qwen25-audit-20260929/audit.json` mengonfirmasi seluruh 1.946
run dan rekonstruksi token prompt tanpa inferensi baru. Penurunan bersih 109
deteksi MAL pada DIFF+I terdiri dari −104 lewat transisi valid/invalid dan
−5 lewat transisi antar-verdict valid. Jangan menyamakannya dengan efek murni
intent terhadap penalaran; batas 512 token dan evidence sebelum verdict
menjadi hambatan keluaran. Angka primer dan snapshot tetap dipertahankan.

**Eksperimen D82 selesai 30 September 2026:** pengguna meminta “Oke lanjutkan experiment tersebut”.
`data/evaluation/output-budget-20260929/evaluate.py` menjalankan seluruh 973
pair pada kedua model dan DIFF/DIFF+I dengan max_tokens 2.048 (3.892 panggilan
baru); kontrol 512 memakai hasil D81 yang dibekukan. Prompt/parser tetap sama,
run key menyertakan anggaran, dan snapshot diverifikasi oleh `preflight.py`.
Periksa `status.json` dan `evaluation.log` sebelum memulai ulang; jangan
menduplikasi controller atau mengganti prompt ketika batch berjalan.
Server dikelola pada port 8101, model bergantian, proses dibersihkan oleh
controller. Setelah selesai, `summarize.py` dan `compare.py` menulis hasil
lengkap serta perbandingan empat kombinasi. Ini eksperimen eksploratif
dengan kontrol historis; tidak menjawab HN/RAG atau mengesahkan G1/G2.

Semua 3.892 respons baru unik dan HTTP 200; checksum 12 artefak eksperimen
dan 12 artefak baseline lolos. Recall sumber 2.048 token: Qwen2.5 DIFF
84,54%, DIFF+I 72,05%; Qwen3 DIFF 54,98%, DIFF+I 63,23%. FPR masing-masing
48%, 49%, 6%, 3%. Seluruh recall naik dari baseline, tetapi FPR Qwen2.5
memburuk. Total invalid 1.077 → 876 dan terpotong 520 → 202; masalah sintaks
tetap besar. Tidak ada perubahan prompt atau parser. Server sudah berhenti.
Lihat `docs/output-budget-20260930.md` untuk dekomposisi, reproduksibilitas,
biaya, dan langkah dev/anotasi sebelum penelitian utama. Jangan menjalankan
inferensi ulang hanya untuk memperbarui laporan; gunakan skrip analisis.

## Spesifikasi konfigurasi

| ID | Isi hasil `retrieve` | Blok intent |
|---|---|---|
| DIFF | `[]` | tidak ada |
| DIFF+I | `[]` | ada |
| DIFF+I+M | 1 card malicious teratas | ada |
| DIFF+I+MM | 2 card malicious teratas | ada |
| DIFF+I+MB | 1 card malicious teratas + 1 card benign teratas | ada |
| DIFF+MB | sama persis dengan DIFF+I+MB | tidak ada |

**Ranking kandidat:**

1. Buang card yang `name` atau `campaign`-nya sama dengan pair. Setelah D88, buang pula nama dependency pada `delta_evidence.dependency_change` dan `retrieval_exclude_names`. Ini filter metadata, bukan intent; sidecar harus digabung ke pair secara eksplisit. Bukti extractor terbatas, jadi jangan mengklaim seluruh dependency transitif/alias/klon sudah terlindungi.
2. Hitung Jaccard pada `delta`, urutkan dari tertinggi.
3. Kalau skor seri, urutkan naik menurut `sha256(f"{pair_id}|{card_id}")`.

**Urutan card untuk DIFF+I+MM, DIFF+I+MB, dan DIFF+MB:**

- Card malicious teratas ditaruh di posisi 1 kalau `zlib.crc32(pair_id.encode()) % 2 == 0`, dan di posisi 2 kalau tidak.
- Jangan pakai `hash()` bawaan Python, karena nilainya diacak per proses.

**Retrieval tidak pernah membaca intent.** Akibatnya DIFF+I+MB dan DIFF+MB selalu
mendapat card dan urutan yang identik.

## Yang masuk dan tidak masuk prompt

- **Dari pair, tidak pernah masuk prompt:** `name`, `delta`, `label`, `gold_evidence`, `subset`, `category`, `campaign`, `source`.
- **Dari card, tidak pernah masuk prompt:** `id`, `delta`, `campaign`, `source`. Label card **justru ditampilkan** (`Example 1 (label: MALICIOUS)`), karena itu yang membuat contohnya kontrastif — methodology §5.1 dan §6.2.
- **Teks prompt** disalin verbatim dari methodology §6.1–§6.2, dalam bahasa Inggris. Jangan diparafrase.
- **Konfigurasi tanpa `I`** (`DIFF` dan `DIFF+MB`): `INTENT_BLOCK` berupa string kosong.
- **Smart-diff** dipotong sekali per pair oleh pipeline data, dengan tokenizer Qwen2.5-Coder-3B-Instruct dan anggaran 28.000 token, lalu disimpan di `pairs.jsonl`. Runner tidak memotong ulang.

## Parsing

1. Cari `{` pertama, lalu baca satu objek JSON dengan `json.JSONDecoder().raw_decode`.
2. Output valid kalau `verdict` bernilai `malicious` atau `benign` (setelah strip dan lowercase), `evidence` berupa list string, dan `reason` berupa string.
3. `finish_reason == "length"` dihitung tidak valid.
4. Runner hanya menyimpan output mentah dan status valid. Kebijakan untuk output tidak valid diterapkan di skrip analisis.

## File data

| File | Ditulis oleh | Dibaca oleh |
|---|---|---|
| `data/wanted.jsonl` | pengumpulan kandidat | `samples.py fetch` |
| `data/samples.jsonl` | `samples.py fetch` | `samples.py extract`, `dataset.py` (checksum) |
| `data/pairs.manifest.jsonl` | pengumpulan + pelabelan | `dataset.py` |
| `data/pairs.jsonl` | `dataset.py` | runner, backend |
| `data/kb.jsonl` | pipeline data | runner |
| `data/dev.jsonl` | pipeline data | runner (dev set, warm-up) |
| `data/results.jsonl` | runner (append per run) | analisis, UI |
| `data/results.dev.jsonl` | runner | pemeriksaan validitas JSON (§6.4) |
| `data/audit_decisions.<annotator>.json` | backend, satu file per annotator | UI, analisis |

Definisi field ada di `docs/experiments.md` §3.

Contoh card **fiktif**:

```json
{"id": "card-b-001", "label": "benign", "campaign": "contoh-cli", "source": "manual",
 "delta": ["network", "host_info"],
 "intent": "Build tool CLI with opt-out anonymous usage statistics.",
 "behavior_chain": "command finishes → collect anonymous counters → HTTPS POST to documented endpoint",
 "code_excerpt": "if (!process.env.CONTOH_TELEMETRY_DISABLED) {\n  send(stats)\n}",
 "rationale": "Runs only after a user command, never at install time. Sends anonymous counters that the README documents and lets users disable."}
```

## Urutan run

**Rantai data** (sebelum model dinyalakan):

1. **Kumpulkan kandidat** sesuai methodology §3.1–§3.3, hasilnya `data/wanted.jsonl`
   (versi yang perlu diunduh) dan `data/pairs.manifest.jsonl` (pair beserta metadata
   dan label). Untuk TYP dan jalur A:
   `python pipeline/typical.py sample --popular <daftar> --random <daftar> --out data/typ.jsonl --pool data/pool.jsonl`
   lalu `python pipeline/typical.py screen --pool data/pool.jsonl --out data/hn_candidates.jsonl`.
   Jalur B memakai `collect.py search` dan `collect.py pairs`.
   Pembagian HN: `python pipeline/hardnegative.py --verified data/hn_verified.jsonl --test data/hn_test.jsonl --cards data/hn_cards.jsonl`.
   Card malicious: `python pipeline/kb.py select --pool <kolam-malicious-intent> --pairs data/pairs.jsonl --out data/kb.mal.jsonl`,
   lalu anotator mengisi `intent`, `behavior_chain`, `code_excerpt`, dan `rationale`,
   dan `python pipeline/kb.py fit --cards data/kb.jsonl --out data/kb.jsonl` menahan ukurannya.
2. **Fetch** — butuh jaringan, di luar container:
   `python pipeline/samples.py fetch --wanted data/wanted.jsonl --out data/samples.jsonl`.
3. **Extract** — tanpa jaringan, di dalam container:
   `python pipeline/samples.py extract --manifest data/samples.jsonl --into work`.
4. **Rakit pairs:** dev set memakai jalur yang sama, hanya manifestnya berbeda
   (§3.5, 10 pair) — tidak ada komponen terpisah untuknya.

   `python pipeline/dataset.py --manifest data/pairs.manifest.jsonl --samples data/samples.jsonl --out data/pairs.jsonl`.
   Diff dipotong di sini, sekali per pair.
5. **Gate G1:** bandingkan jumlah per subset dengan minimumnya, catat di `docs/decisions.md`.

**Inferensi:**

6. **Cek runner:** `python pipeline/runner.py --selfcheck`.
7. **Jalankan server model:**
   `vllm serve <model> --port 8101 --dtype bfloat16 --max-model-len 32768 --seed 0`.
   Catat versi vLLM dan baris log memori bobot model.
8. **Warm-up:** kirim 3 request dari `data/dev.jsonl` ke `--out /dev/null`. Hasilnya tidak dicatat.
9. **Dev set:** `--pairs data/dev.jsonl --out data/results.dev.jsonl`. Periksa validitas JSON (§6.4).
10. **Gate G2:** bekukan desain. Perubahan setelah ini wajib dicatat di `docs/decisions.md`.
11. **Stage 1:** jalankan 6 konfigurasi dengan temperature 0.
12. **Ablasi decoding (D111, menggantikan Stage 2):** T {0; 0,3; 0,7; 1,0} × seed {0,1,2}, top_p 1,
    dua model utama, enam konfigurasi. Jalankan `pipeline/sampling_batch.py --release
    data/evaluation/sampling-ablation-20261109`, lalu `pipeline/sampling_report.py`.
    Lihat `docs/sampling-ablation-20261109.md`. Selesai 12 November 2026; hasil di
    `docs/sampling-ablation-results-20261112.md`. Di WSL, lanjutkan lewat
    `recovery/resume.sh` di release (re-encode U+2028, pelepasan page cache).
13. **Memori:** laporkan memori bobot dari log vLLM ditambah KV cache terhitung (methodology §9.3). Puncak nvidia-smi bukan metrik.

`--base-url` ditulis tanpa `/v1`, default-nya port 8101. Backend di 8100; port 8000 dipakai layanan produksi di mesin GPU.

## Penanganan sampel yang aman

**Isolasi:** ekstraksi, smart-diff, extractor, dan Dolos dijalankan di
`docker run --network none`. Unduhan berada di luar container, jadi urutannya
`samples.py fetch` (butuh jaringan) lalu `samples.py extract` (tanpa jaringan,
D65). `extract` menolak anggota arsip yang keluar dari direktori target atau
berupa link, dan memverifikasi checksum sebelum membuka arsip.

**Versi benign** — untuk pair Wyss ambil dari paket replikasi (kedua sisi ada di zip, D59); untuk sumber lain unduh dari registry, jangan di-install:

```bash
# paket ber-scope: tulis @scope%2Fnama
url=$(curl -s "https://registry.npmjs.org/<nama>/<versi>" | jq -r '.dist.tarball')
curl -sLo pkg.tgz "$url" && shasum -a 256 pkg.tgz
```

**Versi malicious:** `unzip -P infected <sampel>.zip -d <folder>`, dijalankan
di dalam container.

**Dilarang:**

- `npm install`, `npm ci`, `npx`, dan `node <file-sampel>`;
- `require()` atau `import` kode sampel;
- membuka URL atau IP yang muncul di dalam sampel.

## Keluaran skrip analisis

- **RQ1:** recall, FPR_TYP, dan FPR_HN dengan Wilson CI, untuk DIFF dan DIFF+I per model.
- **H2a, H2b, H3:** jumlah pair diskordan (b, c), p exact, p_Holm, Δrecall dengan bootstrap CI per kampanye, dan label hasil.
- **RQ4:** token, median dan p95 latency per konfigurasi, memori minimum terhitung per model, dan Pareto front.
- **Analisis sensitivitas:** output tidak valid dihitung sebagai `malicious`.
- **Subgroup:** delta kosong, `truncated`, pasca-rilis model (EA3), per kategori HN (EA1), per sumber, dan proporsi label card teratas kalau KB dianggap satu kolam campuran (dihitung tanpa inferensi, D61).
