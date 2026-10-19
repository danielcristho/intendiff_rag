# Anotasi sumber dan smart-diff — 250 kandidat HN

`materials.jsonl` berisi identitas, direktori sebelum/sesudah, intent dari
versi sebelumnya, smart-diff, hash diff, dan bukti capability otomatis.
Tidak ada label gold, prediksi model, kategori sinyal, atau kampanye dalam
materi yang ditampilkan. Identitas paket tetap terlihat; ini bukan pembutaan
terhadap reputasi paket.

Anotator manusia A dan B mengisi `annotation.A.jsonl` dan `annotation.B.jsonl`
secara independen. Formulir ditautkan ke `diff_sha256`: jangan mengganti diff
sesudah anotasi tanpa memeriksa kembali evidence. Simpan keputusan awal dan
adjudikasi terpisah. Jangan membuat keputusan dari label sumber/model.

- Untuk tujuan sah, catat kutipan, file, dan versi sumber di `purpose_evidence`.
- Untuk perilaku jahat, catat bukti sumber dan baris smart-diff verbatim di
  `malicious_evidence`. Jangan mengarang baris yang tidak ada pada diff.
- Tentukan kategori HN dari tujuan yang diverifikasi menurut §3.3 metodologi.
- Jika belum jelas, biarkan pending dan jelaskan bagian yang belum terverifikasi.

Periksa batas evidence: 53 diff terpotong pada budget; 15 pair memuat total
74 file yang memakai raw fallback; 6 pair tidak memiliki intent yang tersedia.
Rincian ada di `../normalization-review-flags.jsonl`. Sumber mentah tetap
tersedia lewat path di materi. Baca sebagai teks; jangan menjalankan paket.
Fallback bukan bukti malicious maupun benign. Tidak ada kandidat yang
dihapus otomatis karena batas-batas ini.

Normalisasi ini memakai budget/tokenizer yang berlaku untuk persiapan review.
Audit konteks prompt kedua model dan pembekuan akhir masih diperlukan.
Jika pemotongan akhir mengubah diff, evidence harus diperiksa ulang.

Paket sebelumnya `data/acquisition/hn-annotation-20261013/` dipertahankan.
Jika sudah ada catatan manusia di sana, pertahankan catatan asli dan cocokkan
ke diff ini; jangan menimpanya dengan template kosong.
