# Pemeriksaan data asli melalui UI audit

Data review menggunakan direktori `data/review/`, terpisah dari dataset
eksperimen final. Pair di sini masih kandidat: keberadaannya tidak berarti
telah dipilih sebagai test set atau telah diberi label gold.

UI lokal tersedia di **http://127.0.0.1:5174/**. Per 29 September terdapat
1.035 kandidat pending: 873 MAL dan 162 HN. Lihat
[hasil preprocessing](preprocessing-20260929.md) untuk fallback, pemotongan,
dan batas cakupan kampanye.

## Prosedur anotator

1. Kedua anotator menggunakan identitas berbeda pada gerbang UI dan bekerja
   sendiri sebelum diskusi. UI hanya mengambil keputusan milik identitas aktif.
2. Periksa intent yang berasal dari versi sebelum update, capability delta,
   dan smart-diff. Kode sumber mentah dapat ditemukan melalui `before_dir` dan
   `after_dir` pada manifest review. Jangan menjalankan paket atau URL sampel.
3. Beri label `malicious`, `benign`, atau `skip`. HN memerlukan kategori dari
   **tujuan sah yang diverifikasi**, bukan dari kategori sinyal otomatis. Tulis
   rujukan README/changelog/dokumentasi beserta kutipan pendukung dalam catatan.
4. Untuk MAL, salin baris perilaku berbahaya ke kolom **Gold evidence**, satu
   baris per baris. Pertahankan karakter `+`/`-` dan spasi. UI menolak teks yang
   tidak muncul verbatim pada smart-diff. Anotator A menulis dan B memeriksa;
   jangan menganggap kolom kosong sebagai pemeriksaan selesai.
5. Selesaikan label, kategori, dan catatan sebelum berpindah ke pair berikutnya.
   Gold evidence tersimpan saat fokus keluar dari kolom. Pesan kesalahan berarti
   evidence belum tersimpan. Tombol label berpindah ke pair berikutnya.
6. Setelah kedua anotasi independen lengkap, hitung kesepakatan, diskusikan
   perbedaan, dan catat keputusan konsensus. Pair yang belum disepakati menjadi
   `skip` sesuai §8. Inferensi test set baru dimulai setelah tahap ini dan G2.

Label sumber serta output model tidak ditampilkan sebagai gold pada payload
anotasi. Panel prediksi tidak dimuat untuk pair berstatus `pending`.
Keputusan disimpan oleh backend sebagai `audit_decisions.<identitas>.json`
di direktori review; pipeline tidak membuat atau mengisi berkas tersebut.

## Preprocessing yang sedang digunakan

Versi `static-dolos-exact-v2` adalah rekonstruksi lokal, bukan reproduksi identik
generator Wyss (D72–D74). Webcrack digunakan hanya untuk transformasi statis;
kode berulang dibuang hanya jika jendela fingerprint Dolos mempunyai teks
identik. Perubahan literal dipertahankan. Kode mentah tetap utuh.

Laporan per-file pada field `preprocessing` menunjukkan fallback parsing atau
batas ukuran. File tersebut tetap hadir dalam bentuk mentah. `truncated=true`
berarti tidak seluruh smart-diff masuk anggaran 28.000 token. Jika bukti yang
dibutuhkan tidak tampak atau transformasi meragukan, periksa sumber dan catat
alasan; jangan mengarang gold evidence yang tidak ada pada diff.

`data/acquisition/preprocessing-summary.json` dan `review-exclusions.jsonl`
mencatat hasil serta kandidat yang tidak diterbitkan ke UI. Clustering gabungan
sudah selesai untuk 1.870 item tersedia; perluasan pool KB, verifikasi insiden,
dan pemilihan test/KB masih harus dituntaskan sebelum G1.
