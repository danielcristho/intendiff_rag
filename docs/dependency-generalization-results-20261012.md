# Hasil D89 — tambahan konteks belum menghasilkan perbaikan

Selesai 12 Oktober 2026, 01:09 UTC+7. **30 inferensi nyata** pada 15 target
selesai dan diverifikasi. Qwen3-4B membandingkan NO-SOURCE dengan WITH-SOURCE,
dengan instruksi kondisional nama/versi/section yang sama. Hanya ketersediaan
isi dependency yang berbeda; ini memperbaiki kontrol instruksi dibanding D88.

## Hasil utama

| Cohort | Jumlah target | Malicious tanpa isi dependency | Malicious dengan isi dependency | Transisi |
|---|---:|---:|---:|---|
| HN, label masih pending | 14 | 0 | 0 | 14 benign → benign |
| MAL menurut sumber | 1 | 0 | 0 | 1 benign → benign |

Seluruh 30 respons JSON valid, tanpa length truncation, unknown ID, atau error
transport. Tidak ada perubahan verdict. Satu MAL, `zuper-cli@1.0.1`, tetap
benign ketika diberi konteks `axios@1.6.8`. Model menilai penambahan setup Bun
sesuai tujuan CLI. Penilaian ini belum diverifikasi manusia; label malicious
berasal dari sumber, bukan gold. Label target tidak menjadikan axios malicious.

**Tidak ada bukti kenaikan deteksi pada D89.** Nol alarm HN juga tidak berarti
FPR 0%: label benign belum terverifikasi dan kedua kondisi sudah nol sejak awal.
Hasil ini tidak membatalkan D88, tetapi membatasi generalisasinya: konteks
`easy-day-js@1.11.22` mengubah keputusan pada satu keluarga, sedangkan konteks
dependency yang tersedia di D89 tidak mengubah keputusan.

## Cakupan data dan penyaringan temporal

Dari 1.157 pair praproses, seleksi memakai MAL/HN dengan diff utuh dan dependency
tercatat pada extractor; semua target easy-day-js dikeluarkan. Ada 67 kombinasi
lokal target–versi yang cocok semver (64 HN, tiga MAL dari satu target).

- **44 kombinasi gugur karena dependency terbit setelah target**; tidak ada
  timestamp hilang dalam kelompok ini. Kecocokan rentang versi saja tidak cukup.
- Dua kombinasi self-dependency dikeluarkan, satu versi lokal lebih lama tidak
  dipilih, dan lima kombinasi gugur karena batas satu nama dependency/target.
- Tersisa 15 target dengan 15 nama dependency berbeda: 14 HN dan satu MAL.
  Tidak ada kandidat gugur karena panjang konteks atau kegagalan pembacaan file.
- Enam target sebelumnya masuk paket dev D86. Seluruh target diperlakukan sebagai
  dev; MAL juga pernah terpapar evaluasi historis. Ini bukan holdout baru.

Timestamp berasal dari metadata registry npm yang diperiksa pada 12 Oktober,
bukan bukti versi terpasang. Versi dipilih sebagai yang paling akhir terbit di
antara arsip lokal yang cocok dan tidak melampaui waktu target; bukan resolusi
seluruh registry. Semua keputusan tetap bersyarat pada snapshot itu.

Analisis cakupan setelah inferensi menunjukkan **semua 14 HN hanya memiliki
sinyal delta `dependency_change`**, dan tidak ada snapshot dependency terpilih
yang memiliki install hook. Jadi D89 belum menguji pembanding dengan penambahan
network/process/lifecycle yang sah. Ini keterbatasan data tersedia, bukan alasan
untuk menyebut nol alarm sebagai keberhasilan solusi FPR. Nama dependency berbeda
juga tidak membuktikan 15 insiden atau keluarga kode independen.

## Bukti, biaya, dan verifikasi

WITH-SOURCE hanya menghasilkan dua respons yang mengutip isi dependency:
`has-tostringtag@1.0.2` dan `@tolicodes/picklejs@0.75.0`. Respons lainnya tidak
mengutip isi dependency; kutipan target tetap bisa sah, tetapi bukan bukti bahwa
seluruh konteks dipahami. Keberadaan ID tidak menilai dukungan semantik alasan.

| Kondisi | Token prompt + output | Median latensi HN |
|---|---:|---:|
| NO-SOURCE | 67.749 | 872 ms |
| WITH-SOURCE | 128.286 | 1.195 ms |

Biaya token WITH-SOURCE **1,89×** tanpa perubahan verdict. Total 196.035 token.
Latensi hanya observasi sesi dengan prefix caching, bukan benchmark kausal.
Prompt maksimum 21.401 token; tanpa pemotongan baru dan tanpa warmup generasi.

Audit merekonstruksi seluruh payload/request hash, token prompt, urutan arm,
parsing respons dan kutipan. Sebanyak **91 checksum sumber, 21 input/provenance,
dan 13 berkas model** cocok. Berkas konteks dicocokkan byte demi byte dengan
arsip sebelum pembekuan. Log mencatat 30 generasi HTTP 200 dan dua tokenisasi
HTTP 200; server sudah berhenti. Lima pengujian terfokus lulus.

`data/results.jsonl` penelitian utama tetap tidak dibuat. Tidak ada card KB
berlabel, gold buatan, atau kode sampel yang dieksekusi. Daftar dev-exclusions
tersedia sebagai sidecar; seleksi KB/test mendatang harus menerapkannya dan
memeriksa klon terkait, bukan menganggap loader sudah otomatis melakukannya.

## Implikasi untuk penelitian

D88/D89 dapat ditulis sebagai analisis eksploratif: konteks dependency penting
pada kasus tertentu, tetapi menambahkan konteks yang tersedia tidak otomatis
memperbaiki deteksi. Belum ada bukti penurunan FPR, kenaikan akurasi gold, atau
keberhasilan hipotesis DIFF+I+MB dibanding DIFF+I+MM.

Prioritas berikut lebih spesifik daripada menambah model: lengkapi sumber
**dependency yang berpotensi menjelaskan perilaku target**, beserta HN dengan
perilaku runtime sensitif yang sah. Manifest kekurangan sumber sudah dibuat;
untuk target MAL dengan diff utuh, contoh nama yang belum tersedia adalah
`@antv/setup` (empat target) dan `@opensearch/setup` (dua target). Jumlah ini
menunjukkan cakupan calon, bukan label malicious bagi dependency tersebut.
Arsip dan tanggal harus diverifikasi sebelum konteks masuk eksperimen berikut.

Pengujian utama tetap memerlukan card malicious/benign yang ditulis/diperiksa
anotator A/B, serta pengecualian target, dependency terkait dan klon dari KB.
D89 tidak mengubah default input atau hipotesis studi utama.

Artefak: [protokol](dependency-generalization-20261012.md),
[seleksi](../data/evaluation/dependency-generalization-20261012/selection-summary.json),
[ringkasan](../data/evaluation/dependency-generalization-20261012/summary.json),
[verifikasi](../data/evaluation/dependency-generalization-20261012/verification.json),
[diagnostik](../data/evaluation/dependency-generalization-20261012/diagnostics.json),
[daftar sumber yang kurang](../data/evaluation/dependency-generalization-20261012/missing-dependency-sources.json).
