# Antrean review sumber — 250 kandidat

`materials.jsonl` berisi sumber sebelum/sesudah dan sinyal perubahan otomatis.
Semua path relatif terhadap root proyek. Paket ini belum memuat smart-diff
final dan tidak dapat dipakai langsung sebagai input inferensi.

1. Tetapkan dua manusia berbeda untuk mengisi `annotation.A.jsonl` dan
   `annotation.B.jsonl` secara independen. Jangan saling melihat keputusan.
2. Baca sumber sebagai teks saja. Jangan menginstal atau menjalankan paket.
3. Catat keputusan, tujuan perilaku, kutipan, path, dan versi yang mendukungnya.
   Kategori ditentukan dari tujuan yang diverifikasi, bukan dari sinyal otomatis.
   Gunakan panduan `docs/dataset-expansion-review-20261013.md` dan §8 metodologi.
4. Simpan ketidakpastian sebagai pending; jangan mengisi benign secara default.
   Simpan keputusan awal, lalu adjudikasi secara terpisah.
5. Setelah normalisasi, verifikasi kembali evidence terhadap smart-diff final.

A/B adalah slot formulir, bukan bukti identitas atau independensi anotator.
Belum ada label gold, card KB, atau pembagian HN test/KB final. Template 325
kandidat sebelumnya tidak ditimpa. `summary.json` menyimpan pin input seleksi.
