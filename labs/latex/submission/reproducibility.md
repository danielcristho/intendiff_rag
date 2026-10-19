# Reproduksi IntentDiff-RAG

Berkas pendamping draf 19 Oktober 2026. Ini mendokumentasikan eksperimen yang
sudah dilakukan; tidak menjalankan inferensi baru atau mengubah protokol.
Paket ini tersedia lokal dan belum memiliki tautan arsip publik.

## Masukan dan keluaran yang dipertahankan

| Artefak | Lokasi relatif terhadap root repository |
|---|---|
| Protokol dua model awal, KB, dev, dan respons | `data/evaluation/source-rag-v3-20261015/` |
| Protokol model tambahan dan hasil gate format | `data/evaluation/source-rag-extra-20261016/` |
| Manifest enam model dan evaluasi MAL tambahan | `data/evaluation/source-rag-mal-20261018/` |
| Angka gabungan, selisih, dan verifikasi | `data/writing/paper-20261018/` |
| Normalizer dan dependency lock | `deployments/preprocess/` |
| Sumber naskah | `labs/latex/intendiff-rag.tex` |

Di direktori pendamping ini tersedia:

- `prompt-system.txt`: instruksi sistem dari snapshot eksperimen.
- `prompt-output-format.txt`: instruksi format keluaran dari snapshot yang sama.
- `prompt-builder.py` dan `configs.py`: perakitan pesan serta enam konfigurasi.
- `output-schema.json`: schema yang dikirim sebagai keluaran terstruktur.
- `model-revisions.json`: ID dan revisi penuh keenam model, opsi template,
  stop token, batas konteks, dan KV cache dari protokol tersimpan.
- `metrics.csv`: estimasi titik, interval, sensitivitas respons invalid, dan biaya.
- `contrasts.csv`: selisih berpasangan beserta interval bootstrap.
- `reproduction-checksums.json`: SHA-256 untuk berkas pendamping dan sumber kode terkait.

Prompt dipertahankan sesuai eksperimen. Instruksi format historis mengandung
contoh string “up to 3 lines”, kemudian membatasi evidence menjadi paling
banyak satu baris pendek; schema membatasi array evidence menjadi nol atau
satu string. Ketidakkonsistenan redaksional ini tidak diperbaiki secara
retroaktif atau disembunyikan dengan mengganti snapshot prompt.

## Prosedur yang dapat diperiksa

1. Satu observasi adalah pasangan versi paket yang sama. Pendahulu dipilih
   menurut semver dan waktu publikasi, dengan kedua arsip dan identitas tersedia.
   Label target berasal dari sumber; pemeriksaan advisory pendahulu dan TYP
   tidak membuktikan keamanan atau memberikan label gold manusia.
2. Pemisahan menggunakan nama paket, paparan pengembangan, dan kelompok
   kampanye. Kelompok dibentuk oleh laporan/advisory bersama, berkas baru
   identik, atau kemiripan Dolos minimal 0,5, beserta penutupan transitif.
   Batas tiga pasangan berlaku bagi kampanye MAL yang masih layak; kampanye
   yang dikecualikan tidak dapat diterima hanya karena belum mencapai batas.
   Manifest pengecualian tetap tersimpan bersama masing-masing akuisisi.
3. `pipeline/source_cohort.py` membentuk KB secara deterministik: hash-order
   `SHA256("D99|" + id)`, pemilihan malicious bergiliran menurut delapan
   kemampuan, maksimal dua kartu per kampanye, kemudian reservasi 25 kartu
   benign dari TYP. Seluruh nama dan kampanye kartu dikeluarkan dari test.
   `source_cards.py` memakai kemampuan versi sumber untuk kedua label.
4. Normalisasi menggunakan UglifyJS 3.19.3, webcrack 2.16.0, dan Dolos 3.5.1.
   Eksekusi sampel dinonaktifkan. Pengurangan kode memakai k-gram 70 dan
   jendela 17, menghapus interior fragmen identik dengan pemeriksaan teks
   batas. Diff memakai `diff -N -U 0 -r`. Berkas gagal normalisasi atau di atas
   4 MiB memakai teks mentah. Eksklusi lengkap berada di `normalization.py`:
   `*.wasm`, `*.md`, `*.map`, `.npmignore`, `LICENSE*`, `license*`,
   `*.tsbuildinfo`, `package-lock.json`, dan `yarn.lock`.
5. Diff dibatasi 2.000 karakter per baris dan 28.000 token Qwen2.5-Coder-3B.
   Manifest didahulukan, diikuti jumlah jenis kemampuan per berkas, lalu path.
   Pemotongan dilakukan pada hunk. Intent: 1.024 token; deskripsi dan kata
   kunci berbagi 128 token, skrip 256 token, README mengisi sisanya.
6. Kueri retrieval memuat kemampuan baru, perubahan hook instalasi, dependensi
   baru atau berubah ke sumber non-registry, serta penghapusan minimal 50%
   berkas teks. Kemampuan kartu berasal dari versi paket utuh. Skor Jaccard
   kosong bernilai nol; pemecah seri adalah SHA-256 `pair_id|card_id`.
   M, MM, dan MB mengambil urutan terbaik per label tanpa pengulangan kartu.
   Posisi contoh malicious utama ditentukan paritas CRC32 identitas pasangan.
7. Inferensi: RTX 5090 sekitar 32 GiB, vLLM 0.30.0, bfloat16, temperature 0,
   seed 0, maksimum keluaran 512 token, satu request aktif, prefix caching.
   Nilai konteks per model dan opsi template mengikuti protokol. Revisi
   tokenizer dibekukan bersama revisi model. Temperature nol dan satu seed
   tidak menjamin determinisme lintas GPU atau versi server.
8. Respons invalid dianggap benign pada analisis utama dan malicious pada
   sensitivitas. Error transport bukan prediksi. Bootstrap memakai 10.000
   resample, seed 2026, persentil 2,5 dan 97,5; pasangan pada klaster yang
   terpilih diambil bersama. Untuk selisih, kedua konfigurasi memakai resample
   yang sama. Interval bersifat deskriptif dan tidak dikoreksi untuk
   perbandingan berganda. Terdapat 98 kelompok MAL dan 1.865 kelompok TYP.

## Menghasilkan angka dan gambar

Dari root repository, pada lingkungan proyek yang dependensinya tersedia:

```bash
.venv/bin/python pipeline/paper_results.py
.venv/bin/python -m unittest discover -s tests -p 'test_paper_results.py'
```

Exporter membaca respons tersimpan dan memeriksa kelengkapan, duplikasi,
identitas, serta hitungan prediksi. Perintah ini tidak memanggil model.
Tabel utama naskah berisi estimasi titik sesuai pilihan penyajian penulis;
interval lengkap tetap disediakan di CSV dan gambar. Berkas LaTeX hasil
exporter berada di `labs/latex/generated/` dan tidak dimuat oleh naskah aktif.
Jangan menimpa tabel naskah secara otomatis tanpa meninjau formatnya.

PDF gambar bersifat vektor dengan font tertanam. PNG 300 dpi digunakan untuk
pratinjau dan TIFF 1.000 dpi tersedia untuk kebutuhan line art. Angka gambar
diambil dari `contrasts.csv`; teks pada gambar berbahasa Inggris.

Instruksi build naskah ada di `../BUILD.md`. Tree LaTeX di `/tmp` bersifat
sementara dan harus tersedia kembali pada mesin/sesi lain.

## Batas verifikasi dan publikasi

Checksum dan pemeriksaan hitungan tidak memvalidasi label secara semantik.
Belum ada audit gold manusia, pengulangan lintas seed, pengujian temporal
terkontrol, atau evaluasi pembanding pada dataset yang sama. Perluasan model
dan MAL setelah hasil awal diketahui tetap dicatat sebagai keterbatasan.

Sebelum submission, penulis perlu menyediakan akses anonim bagi reviewer
atau DOI repositori, memastikan hak distribusi setiap artefak, serta
menetapkan kebijakan rilis data malicious. Tidak ada berkas yang diunggah atau
dibagikan ke layanan eksternal selama penyuntingan ini.
