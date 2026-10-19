# Eksperimen akhir berbasis dataset — D99

Pengguna memilih melanjutkan tanpa kewajiban anotasi dua manusia. Ini revisi
metode sebelum inferensi RAG, bukan penggantian label berdasarkan hasil model.
Aturan di dokumen ini mengungguli persyaratan anotasi/card ahli/HN pada rancangan
lama. Snapshot D81–D98 dipertahankan.

## Data dan klaim

- MAL menggunakan label malicious dari dataset sumber. Simpan record asal,
  versi, hash file sumber dan arsip, bukan flag gold manusia.
- TYP menggunakan asumsi benign dari sampling typical dengan pemeriksaan
  advisory kedua versi. Recall/TPR MAL disebut recall label sumber; FPR TYP
  dan akurasi bersyarat pada asumsi label tersebut. Laporkan balanced accuracy,
  komposisi kelas, invalid, dan sensitivitas invalid sebagai malicious.
- 250 HN pending bukan benign otomatis. Bahan yang sudah dibuat tetap berguna
  sebagai kohort diagnostik, terpisah dari confusion matrix. Ukur tingkat alarm
  dan transisi berpasangan; jangan menyebutnya FPR_HN atau hard-negative gold.
- Data yang sudah dipakai eksperimen tetap dev. Data baru wajib diperiksa
  terhadap seluruh pool/kampanye lama; hash/nama berbeda tidak cukup.
- Hasil utama holdout membutuhkan MAL independen yang benar-benar lolos.
  Jika tidak tersedia, batch MAL dev + TYP hanya menjawab evaluasi sumber
  dengan keterbatasan paparan; tidak diganti namanya menjadi holdout.

## RQ operasional dan matriks

Enam konfigurasi tetap `DIFF`, `DIFF+I`, `DIFF+I+M`, `DIFF+I+MM`,
`DIFF+I+MB`, `DIFF+MB`; dua model utama tetap Qwen3-4B-Instruct-2507 dan
Qwen2.5-Coder-3B-Instruct. Tidak memilih model berdasarkan TPR D92.

RQ1: deteksi pada MAL sumber dan TYP assumed-benign. RQ2: perubahan recall
dan FPR TYP saat menambahkan M dan mengganti contoh kedua MM menjadi MB.
RQ3: pengaruh intent pada pasangan MB dengan/tanpa intent. RQ4: token,
latency dan biaya sesuai pengukuran semula. Semua perbandingan paired.

Ini mengubah cakupan RQ2/RQ3: hasil tidak menguji hipotesis awal mengenai
hard negative yang telah diverifikasi. Perbandingan utama D99 dilaporkan
deskriptif dengan interval ketidakpastian; tidak menyalin label keberhasilan
H2/H3 konfirmatori atau menjanjikan penurunan recall ≤5 poin dari estimasi
titik. Bukti verbatim ke diff dapat diukur, tetapi bukan evidence localization
terhadap gold. Tidak melaporkan κ tanpa anotator.

## Card berbasis sumber

Target 50 malicious dan 25 assumed-benign; pemilihan deterministik sebelum
prediksi. Gunakan urutan capability/hash dan maksimal dua per kampanye.
Card benign berasal dari TYP yang direservasi untuk KB, bukan HN pending.
Seluruh nama/kampanye yang masuk KB dikeluarkan dari calon test. Kuota 5 per
kategori HN tidak berlaku karena kategori sah belum diketahui.

Kedua label menggunakan pembuat card yang sama: deskripsi paket verbatim,
daftar temuan capability statis (bukan klaim rantai eksekusi), kutipan kode
verbatim dengan file/baris/hash, dan rationale tetap yang menyatakan label
referensi dataset serta keterbatasan validasi. Tidak membuat penjelasan
kejahatan/tujuan sah yang tidak didukung sumber. Metadata sumber tidak
ditampilkan ke model. Ini contoh berlabel yang diekstrak otomatis, bukan
KB penalaran ahli IntelGuard. Efek representasi card merupakan keterbatasan.

Batas tetap 15 baris/512 token per card dan intent 64 token. Pemangkasan
hanya pada batas baris/teks yang tercatat; record yang tidak bisa memenuhi
batas dicatat sebagai attrition dan diganti sesuai urutan tetap. Tidak memakai
prediksi target untuk memilih contoh. MM/MB mempertahankan anchor/posisi;
MB dengan/tanpa intent harus identik. Eksklusi nama, kampanye, dependency,
dan daftar eksplisit tetap berlaku.

## Syarat menjalankan

G1 kini memeriksa provenance label, attrition, jumlah dan independensi kampanye,
serta menetapkan cakupan klaim; tidak menunggu dua anotator. G2 memeriksa seluruh
matriks retrieval, sumber kutipan, budget dua tokenizer, pin model/kode/input,
dan validitas dev. Tidak mengubah prompt berdasarkan test. Pemeriksaan parsial
`final_readiness.py` belum menjadi peluncur inferensi.

Simpan protokol, pembagian, card, prompt, daftar panggilan yang diharapkan, dan
hash sebelum inferensi. Gunakan direktori baru; D92 tetap eksperimen tanpa RAG.
Seluruh kombinasi yang dilaporkan harus benar-benar berjalan dan diverifikasi.
Anotasi manusia opsional untuk memperkaya penelitian, bukan pekerjaan wajib
yang dilempar kembali ke pengguna.

## Pemeriksaan format dev (D100, 15 Oktober)

Qwen3 pada dev awal hanya 45/60 JSON valid. Sesuai §6.4, satu revisi instruksi
format diterapkan untuk kedua model/seluruh konfigurasi: evidence paling banyak
satu baris pendek verbatim atau `[]`, JSON escaping tepat sekali, reason <30
kata. System prompt dan aturan keputusan tidak berubah. Snapshot dev pertama
utuh; hasil dev revisi disimpan terpisah. Test tidak dijalankan sebelum audit
format dan input selesai.

Untuk D99, capability card memakai temuan statis pada versi contoh, dengan
pembuat sama untuk M dan B; delta target tetap perubahan antarversi. M dipilih
round-robin capability/hash, B mengikuti hash-order TYP eligible dan syarat
kutipan. FPR TYP dilaporkan terpisah untuk popular, random dan stream. Akurasi
cohort bergantung pada rasio kelas dan bukan estimasi prevalence dunia nyata.
