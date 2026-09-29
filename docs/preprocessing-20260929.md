# Hasil preprocessing data asli — 29 September 2026

**1.157 pair selesai diproses, tanpa error pair.** Ini hasil preprocessing
korpus asli, belum hasil akurasi model. Tidak ada inferensi dev/test set pada
batch ini, dan `data/results.jsonl` belum dibuat. Riwayat akuisisi ada dalam
[laporan 28 September](real-data-20260928.md).

## Hasil dan batasan

| Bagian | Pair diproses | Diff terpotong | Pair dengan fallback | Kandidat review |
|---|---:|---:|---:|---:|
| MAL Wyss + Datadog | 875 | 327 | 324 | 873 |
| HN jalur A | 182 | 31 | 8 | 162 |
| TYP | 100 | 14 | 0 | — |
| Total | 1.157 | 372 | 332 | 1.035 |

Sebanyak 346 file memerlukan fallback: 321 melewati batas transformasi 4 MiB,
8 bukan UTF-8, dan 17 gagal parsing atau transformasi. Fallback mempertahankan
kode mentah; angka nol error pair tidak berarti semua file berhasil
dinormalisasi. Seluruh diff memiliki isi. Jumlah token maksimum 27.999,
di bawah anggaran 28.000 termasuk marker pemotongan.

Preprocessing `static-dolos-exact-v2` memakai UglifyJS 3.19.3, Webcrack 2.16.0,
dan Dolos 3.5.1, dengan k-gram 70/window 17. Webcrack tidak mengeksekusi
deobfuscation atau unpacking. Hanya interior baris pada jendela teks identik
yang dihapus; perubahan literal dipertahankan. Semua pemrosesan kode sampel
berjalan statis dalam container tanpa jaringan. Kode asli tidak diubah.
Ini **rekonstruksi lokal**, bukan reproduksi identik Wyss karena `index.mjs`
upstream tidak tersedia (D72–D76).

Jumlah token dan SHA-256 diff seluruh 1.157 pair diperiksa ulang secara
independen. Tokenizer berasal dari Qwen2.5-Coder-3B-Instruct revisi
`488639f1ff808d1d3d0ba301aef8c11461451ec5`, dengan SHA-256 `tokenizer.json`
`c0382117ea329cdf097041132f6d735924b697924d6f6fc3945713e96ce87539`.
Tokenizers 0.23.2 memberikan token yang sama dengan AutoTokenizer pada empat
probe, termasuk Unicode dan token khusus.

Median panjang diff adalah 2.133 token untuk MAL, 2.157 untuk HN, dan 593
untuk TYP. Pemotongan pada batas hunk dapat menghasilkan diff jauh di bawah
anggaran jika hunk berikutnya terlalu besar. Fallback tidak tersebar merata
(324/875 MAL, 8/182 HN, 0/100 TYP); perbedaan ini merupakan keterbatasan
perbandingan antarsubset, bukan bukti kualitas klasifikasi model.
[Grafik PNG](../figures/preprocessing-20260929.png) dan
[PDF](../figures/preprocessing-20260929.pdf) memakai kandidat asli.
Statistiknya disimpan di `preprocessing-distributions.json`.

## Kampanye

Clustering berhasil untuk semua **1.870 item tersedia**: 875 kandidat MAL dan
995 entri KB dengan identitas valid. Dua kegagalan resource pada percobaan
awal berhasil diselesaikan; keluaran lengkap adalah
`combined-campaigns-complete.json`.

| Ambang Dolos | Jumlah klaster |
|---|---:|
| 0,5 | 714 |
| 0,8 | 735 |

Pemetaan ambang 0,5 sudah ditambahkan ke kandidat MAL. Cakupan hasil awal masih
prefix 1.000 arsip dari 24.324 versi malicious-intent, dengan lima mismatch
identitas dikeluarkan. Ini belum pemetaan kampanye seluruh pool, belum
pemilihan 50 card final, dan belum bukti bahwa test/KB final bebas kebocoran.
Penambahan anggota pool atau laporan insiden dapat menggabungkan klaster.

**Kelanjutan pool penuh:** seluruh **24.324 arsip** (16.529.176.471 byte)
telah diunduh dari snapshot yang sama. Seluruh SHA-256 dan Git blob SHA-1
diperiksa ulang, tanpa kegagalan unduhan. Inventaris menghasilkan **24.198
entri valid** dan **126 pengecualian**: 102 tidak memiliki `package.json`
dengan identitas yang cocok, 24 memiliki dua kandidat manifest yang cocok.
Identitas ambigu tidak dipilih dengan tebakan. Hasil dan ID pengecualian
tersimpan di `kb-pool-verification.json`.

**Clustering penuh selesai:** seluruh 25.073 item berhasil tanpa kegagalan
fingerprint, menghasilkan **3.681 klaster pada 0,5** dan **4.114 pada 0,8**.
Pemetaan dalam `combined-campaigns-full.json` sudah diterbitkan ke paket review.
Tahap otomatis berakhir dengan status `prepared_for_human_review`.

Pemeriksaan advisory mencakup 25.154 kombinasi versi tepat (pool KB penuh
dan kandidat Datadog MAL). Pembuatan material dan clustering penuh mencakup
untuk **25.073 item**: 875 MAL + 24.198 KB valid. Status terbaru tersedia di
`full-kb-pipeline-state.json`; jumlah klaster 714/735 di atas tetap merujuk
hasil prefix. Proses otomatis memverifikasi
input, membuat material, menghitung klaster, lalu menerbitkan pemetaan baru
ke paket review hanya jika seluruh fingerprint berhasil. Ia tidak mengisi
keputusan anotator atau memulai inferensi.

Batas EA3 menurut D58/D78 sudah dicatat: **6 November 2024** untuk
Qwen2.5-Coder-3B dan **5 Agustus 2025** untuk Qwen3-4B-Instruct-2507.
Riwayat commit resmi dan card diarsipkan; tanggal insiden kampanye masih
perlu diverifikasi. Sufiks nama model `2507` bukan tanggal cutoff.

## Kesiapan model dan konteks

Qwen3-4B-Instruct-2507 sudah diunduh pada revisi
`cdbee75f17c01a7cc42f958dc650907174af0554`. Checksum 13 berkas, termasuk
tiga shard safetensors, tercatat di `qwen3-model-provenance.json`. Bobot
tersedia lokal; inferensi belum dimulai.

Tokenisasi offline seluruh 1.157 prompt **DIFF+I** menggunakan chat template
lokal kedua model menghasilkan panjang maksimum yang sama: **29.342 token**.
Setelah mencadangkan jawaban 512 token, tersisa sekurangnya **2.914 token**
dari konteks 32.768; tidak ada prompt baseline yang melampaui batas.
Ini pemeriksaan masukan asli tanpa panggilan model. Prompt retrieval masih
harus dihitung kembali sesudah card selesai ditulis. Rincian per pair ada
di `context-audit-baselines.jsonl` dan `context-audit-summary.json`.

## Paket anotasi yang tersedia

UI lokal: **http://127.0.0.1:5174/**. Backend lokal: port 8100.
Paket review berada di `data/review/pairs.jsonl`, berisi **873 MAL + 162 HN**,
seluruhnya pending. Dua MAL gagal syarat predecessor bebas advisory; 20 HN
gagal pemeriksaan advisory atau penerbit sama. TYP tidak memerlukan label
ganda menurut §8.

Tidak ada berkas keputusan anotator yang dibuat otomatis. Label sumber dan
prediksi tidak dikirim sebagai label gold. UI menyediakan intent terstruktur,
kategori HN, catatan, serta evidence verbatim. Informasi asal dan direktori
kode mentah tetap tersedia pada manifest. Ikuti
[panduan anotasi](annotation-20260928.md).

## Verifikasi dan artefak

- **21/21 pemeriksaan pipeline** lulus, termasuk analisis statistik dan
  pengaman runner terhadap input hilang. Ini uji implementasi, tanpa panggilan
  LLM. Runner tidak lagi mengganti berkas penelitian yang hilang dengan fixture.
- **16 tes frontend**, pemeriksaan tipe dan build produksi lulus;
  **13 tes backend** lulus. UI mengembalikan HTTP 200, health backend `ok`,
  dan daftar anotator masih kosong saat diperiksa.
- `data/acquisition/pairs.prepared.jsonl`: kandidat dengan smart-diff,
  intent, provenance, token, fallback, serta metadata kampanye MAL.
- `preprocessing-summary.json`, `preprocessing-quality.json`, dan
  `review-exclusions.jsonl`: ringkasan serta pemeriksaan isi.
- `combined-campaigns-full.json`: pemetaan kampanye seluruh 25.073 item;
  `combined-campaigns-complete.json` adalah hasil historis untuk prefix.
- `model-release-cutoffs.json`: bukti batas EA3 dan checksum sumber.
- `pipeline-checks-20260929.json`, `audit-backend-tests.log`,
  `image-provenance-20260929.json`, dan `artifact-manifest-20260929.json`:
  hasil pemeriksaan, identitas image, dan checksum artefak.
- `artifact-manifest-review.json` dibuat ulang setiap penerbitan paket review,
  termasuk setelah pemetaan kampanye penuh tersedia. Keputusan manusia tidak
  dimasukkan atau ditimpa oleh penerbitan ini.

## Syarat sebelum evaluasi penelitian

G1/G2 masih terbuka. Akuisisi pool dan clustering penuh telah selesai.
Yang tersisa adalah verifikasi kampanye/insiden; dua anotasi independen
MAL/HN, κ dan konsensus; pembagian
test/KB/dev sesuai kuota; serta penulisan card oleh A dan pemeriksaan B.
Metodologi §8 menetapkan: **“seluruh pelabelan selesai sebelum model dijalankan
pada test set.”** Label sumber saja tidak memenuhi syarat itu.

Atas persetujuan pengguna, D81 menetapkan evaluasi eksploratif terpisah:
973 pair (873 MAL berlabel sumber + 100 TYP diasumsikan benign), dua
konfigurasi baseline dan dua model. Protokol dan hasilnya berada di
[`data/evaluation/source-baselines-20260929/`](../data/evaluation/source-baselines-20260929/).
Evaluasi ini tidak menyatakan G1/G2 selesai dan tidak memakai label HN atau
card KB yang belum diverifikasi.
