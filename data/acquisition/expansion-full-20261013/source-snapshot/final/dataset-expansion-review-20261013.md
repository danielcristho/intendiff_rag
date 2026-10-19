# Review kandidat perluasan dataset

Status seluruh berkas berikut adalah **kandidat**, bukan gold atau test set
final. Tidak ada inferensi model baru pada kandidat tambahan.

## Bahan

- TYP popular/random yang disaring ulang:
  `data/acquisition/expansion-full-20261013/review.typical.jsonl`.
- TYP dari stream update, dengan nama paket yang belum dipakai:
  `data/acquisition/typical-stream-20261013/review.typical.jsonl`.
- HN jalur B yang lolos pemeriksaan otomatis:
  `data/acquisition/expansion-full-20261013/review.hn.jsonl`.
- Gabungan HN lama dan baru yang lolos pemeriksaan otomatis (325 pair):
  `data/acquisition/expansion-full-20261013/review.hn-combined.jsonl`.
- Gabungan ketiga strata TYP (2.257 pair):
  `data/acquisition/expansion-full-20261013/review.typical-combined.jsonl`.
- Template kosong untuk dua anotator:
  `data/acquisition/expansion-full-20261013/annotation-template.combined.A.jsonl`
  dan `annotation-template.combined.B.jsonl`. Template bukan bukti anotasi selesai.

Setiap pair menunjuk direktori versi sebelum/sesudah. Pada HN, `delta_evidence`
memuat lokasi sinyal, dan `purpose_documents_before/after` memuat nama berkas
README/CHANGELOG yang tersedia. Kehadiran dokumentasi bukan bukti tujuan sah.
`advisory_checks` menyimpan waktu dan hasil pemeriksaan kedua versi.

## Prosedur anotasi

1. A dan B menilai sumber secara independen, tanpa melihat keputusan satu sama
   lain atau prediksi LLM. Jangan menjalankan package, install hook, atau script.
2. Periksa apakah perilaku baru memang terjadi, apa yang memicunya, tujuan
   data/jaringan/prosesnya, serta apakah dokumentasi menjelaskan tujuan sahnya.
   Catat kutipan, path, dan versi dokumentasi yang mendukung keputusan.
3. Tentukan label dan kategori dari tujuan perilaku. `signal_categories` adalah
   hasil penyaring yang dapat tumpang tindih, bukan kategori gold. Publisher
   sama dan advisory kosong tidak cukup untuk menerima kandidat sebagai HN.
4. Kasus tidak jelas tetap `pending` atau ditolak dengan alasan yang dapat
   ditelusuri. Jangan mengganti label dengan verdict otomatis.
5. Hitung kesepakatan sebelum adjudikasi. Simpan keputusan awal A/B, lalu hasil
   adjudikasi terpisah. Card KB ditulis/diperiksa setelah sumber diverifikasi.

Gold evidence berbasis smart-diff dibuat setelah normalisasi final. Bahan batch
ini mencakup sumber dan bukti capability; ia belum menjadi input inferensi
ternormalisasi yang dibekukan. Jangan memasukkannya langsung ke runner sebagai
test set dengan label benign buatan.

## Split dan pelaporan

- Terapkan daftar paparan `exposure-registry.jsonl`, identitas package dan
  dependency, lalu clustering gabungan klon/kampanye sebelum membagi dev/test/KB.
  `holdout_eligible=false` sengaja dipertahankan sampai pemeriksaan itu selesai.
- TYP baru dari stream adalah strata berbeda. Laporkan popular, random, dan
  stream terpisah; tetapkan bobot sebelum membuat satu angka FPR gabungan.
- TYP lama yang juga merupakan kandidat HN ditandai `overlaps_hn`. Jangan
  menjumlahkan keduanya sebagai observasi independen atau menghapus HN dari
  TYP untuk memperkecil FPR.
- Batch penuh HN bersifat kumulatif dan mencakup batch awal. Jangan menjumlahkan
  kedua batch. Jumlah sinyal per kategori juga dapat melebihi jumlah pair.
- Seluruh MAL yang sudah dievaluasi tetap dev terpapar. Batas tiga pair per
  kampanye tidak mengubah status paparan. Dua versi baru pada manifest Datadog
  tanpa arsip belum merupakan tambahan pair MAL yang dapat dievaluasi.
