# Ablasi temperature × seed — D111

Diminta dosen pembimbing pada 9 November 2026. Seluruh hasil utama naskah
(D101, D102, D105) dijalankan sekali dengan decoding greedy: temperature 0,
seed 0, top_p 1. Akibatnya, naskah belum bisa menjawab apakah temuan
bergantung pada setelan decoding, dan keterbatasan "satu run, satu seed"
masih terbuka. Ablasi ini menambahkan temperature dan seed sebagai faktor
yang divariasikan. Hasil utama tidak diganti.

## Pertanyaan yang dijawab

1. **Seed pada T=0.** Apakah verdict greedy benar-benar sama di seed 0, 1, dan 2?
   Seharusnya sama. Kalau berbeda, sumbernya nondeterminisme server, bukan seed.
2. **Pengaruh temperature.** Bagaimana TPR (129 MAL) dan FPR (1.868 TYP)
   bergeser dari T=0 ke 0,3, 0,7, dan 1,0?
3. **Stabilitas antar seed.** Pada tiap temperature, berapa proporsi pair yang
   verdict-nya tidak sama di ketiga seed (flip rate), dan seberapa lebar rentang
   TPR/FPR antar seed?
4. **Ketahanan kontras.** Apakah arah ketiga kontras konfigurasi
   (DIFF+I → DIFF+I+M, DIFF+I+MM → DIFF+I+MB, DIFF+MB → DIFF+I+MB) sama dengan
   sel referensi di setiap sel grid?

## Desain

| Faktor | Level |
|---|---|
| Temperature | 0; 0,3; 0,7; 1,0 |
| Seed (per request) | 0, 1, 2 |
| Model | Qwen3-4B-Instruct-2507, Qwen2.5-Coder-3B-Instruct |
| Konfigurasi | keenam konfigurasi D62 |
| Data | 1.997 pair test naskah: 1.901 dari D101 + 96 MAL dari D105 (129 MAL / 98 kampanye, 1.868 TYP) |

Grid penuh berisi 12 sel per model. Satu sel memuat 1.997 × 6 = 11.982 respons,
jadi totalnya 11.982 × 12 × 2 = **287.568 respons**. Dari latensi run D101/D105
di RTX 5090, satu sel butuh ±4,2 jam untuk kedua model, sehingga total ±50 jam
GPU. Runner bisa dilanjutkan setelah berhenti, jadi pekerjaan boleh dicicil.

**Yang berubah hanya temperature dan seed.** top_p tetap 1 dan top_k tidak
dikirim, sehingga pada T>0 model mengambil sampel dari distribusi penuh yang
diskalakan temperature. Prompt, KB, retrieval, schema JSON D101, budget 512 token,
parser, aturan invalid, flag server, dan revisi bobot sama byte-for-byte dengan
D101/D105. Kode pembentuk request disalin dari snapshot D101 dan diperiksa
identik sebelum pembekuan.

**Cakupan model.** Hanya dua model utama, yang ditetapkan sejak D99. Lima model
lain ditambahkan sesudah hasil awal diketahui (D102) dan tetap hanya punya hasil
T=0. Naskah tidak boleh mengklaim ketahanan decoding untuk kelima model itu.

**Sel referensi dijalankan ulang.** Sel (T=0, seed 0) ikut dijalankan lagi di
snapshot ini, tidak diambil dari hasil historis. Alasannya, lingkungan inferensi
harus dipasang ulang (lihat Status), dan D54 menunjukkan bahwa greedy pun bisa
bergeser antar build. Pembandingan antar sel dilakukan di dalam snapshot ablasi.
Kesesuaian sel referensi dengan run historis dilaporkan per pair sebagai
pemeriksaan reproduksi: kesamaan verdict dan kesamaan teks mentah.

**Menggantikan Stage 2 / D11.** Rencana lama (T 0,7, top_p 0,8, top_k 20, tiga
seed, hanya DIFF+I dan DIFF+I+MB) tidak pernah dijalankan. Rencana itu mengubah
tiga parameter sekaligus dan hanya mencakup dua konfigurasi, sehingga tidak bisa
menguji kontras.

## Kondisi inferensi

- vLLM 0.30.0, torch 2.13.0, transformers 5.17.0, tokenizers 0.23.2,
  jsonschema 4.26.0, numpy 2.3.5, xgrammar 0.2.8, Python 3.12.9. Nilainya diambil dari
  `runtime-observation.json` D101. Batch menolak berjalan kalau `.venv` berbeda.
- Flag server sama dengan D105 (`source_experiment.serve_command`): BF16,
  konteks 32.768, KV 6 GiB, `--seed 0`, `--generation-config vllm`,
  `--max-num-seqs 1`, prefix caching. Seed per request mengambil alih seed server.
- Satu sesi server per model, dan 12 sel dijalankan berurutan di dalamnya.
  Warm-up 3 request pada T=0 dicatat tetapi tidak dinilai.
- Gate format dev tidak diulang. Gate itu sudah lolos pada T=0 untuk prompt dan
  schema yang sama. Validitas JSON pada T>0 merupakan hasil, dilaporkan per sel,
  dan tidak dipakai untuk menggugurkan sel.
- Pin bobot model diperiksa sebelum dan sesudah setiap model. Setiap sel
  diverifikasi ulang dengan `source_results.verify`, yang merekonstruksi hash
  request lengkap termasuk seed dan temperature.

## Analisis

Semua metrik memakai definisi naskah: invalid dihitung benign (sensitivitas
invalid sebagai malicious dilaporkan), bootstrap per kampanye dengan 10.000
resample dan seed 2026.

| Keluaran | Isi |
|---|---|
| `metrics.csv` | TPR dan FPR beserta CI kampanye per model × temperature × seed × konfigurasi; invalid; token; latensi |
| `stability.csv` | rerata, minimum, dan maksimum TPR/FPR antar seed; flip rate seluruh pair, MAL, dan TYP per model × temperature × konfigurasi |
| `contrasts.csv` | ΔTPR dan ΔFPR berpasangan beserta CI untuk ketiga kontras di tiap sel, ditambah apakah tandanya sama dengan sel referensi |
| `summary.json` | reproduksi sel referensi terhadap run historis per konfigurasi; jumlah respons |

**Interpretasi.** Ablasi ini deskriptif. Ablasi ini tidak dipakai untuk memilih
setelan decoding "terbaik" bagi hasil utama, karena itu berarti menyetel pada
test set. Kalau temperature tertentu memberi TPR lebih tinggi, angka itu
dilaporkan apa adanya sebagai hasil ablasi, dan tabel utama tetap T=0. Tiga seed
cukup untuk mendeteksi ketidakstabilan, tetapi tidak cukup untuk menaksir
variansnya dengan presisi.

**Batasan.** Pada T>0 sampling berlangsung di dalam constrained decoding
(xgrammar), jadi distribusi yang diambil sampelnya sudah dipotong oleh schema.
Reproduksibilitas seed per request terikat pada versi vLLM dan GPU (D54).

## Status dan cara menjalankan

Kode siap dan diuji dengan server tiruan. **Belum ada inferensi.** Saat protokol
ini ditulis, `.venv` (vLLM) dan bobot model di `data/upstream/models/` serta
cache HF Qwen2.5-Coder-3B tidak ada lagi di mesin. Keduanya harus dipasang ulang
pada versi dan revisi yang dipin.

```
python pipeline/sampling_prepare.py --out data/evaluation/sampling-ablation-20261109   # bekukan input
python pipeline/sampling_batch.py --release data/evaluation/sampling-ablation-20261109  # ±50 jam, resumable
python pipeline/sampling_report.py --release data/evaluation/sampling-ablation-20261109
```

Jalankan dari root repo (`.venv/bin/vllm` dicari relatif terhadap direktori kerja).
Sampel hanya dianalisis secara statis. Runner hanya mengirim teks diff ke
server lokal, dan tidak ada paket yang dipasang atau dieksekusi.
