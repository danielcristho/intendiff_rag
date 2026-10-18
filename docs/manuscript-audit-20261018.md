# Audit naskah berbasis eksperimen, 18 Oktober 2026

Naskah aktif `labs/latex/intendiff-rag.tex` ditulis ulang mengikuti
D99/D101/D102/D105, dalam Bahasa Indonesia. Abstrak, pendahuluan, penelitian
terkait, metode, rancangan, hasil, pembahasan, keterbatasan, kesimpulan,
ketersediaan artefak, dan lampiran telah terisi. Tidak mengubah protokol,
prompt, KB, atau model, dan tidak menjalankan inferensi baru.

## Bukti angka

D105 sudah lengkap: enam model × 576 = 3.456 respons baru, nol error transport.
D101/D102 menyumbang 68.436 respons test. Total 71.892 respons berasal dari
1.997 pasangan unik, bukan 71.892 sampel independen. Qwen3-8B tetap dicatat
gagal gate dev, 49/60 valid. Tambahan 96 MAL/65 klaster dipisahkan dari 33 MAL
awal; gabungan 129 MAL/98 klaster bukan 129 kasus baru yang independen.

`pipeline/paper_results.py` menghasilkan `metrics.csv`, `contrasts.csv`, dan
`verification.json` di `data/writing/paper-20261018/`. Pemeriksaan mencakup
coverage dan duplikasi, identitas model/pair/label/diff, validitas JSON agregat,
confusion matrix kedua kebijakan invalid, akurasi/BA gabungan, token, dan latensi
dari respons mentah. Semua cocok dengan ringkasan tersimpan. Ini bukan klaim
audit semantik label manusia atau pemeriksaan ulang seluruh bobot model.

CI berasal dari analisis D105: bootstrap 10.000 resample kampanye, seed 2026.
Tidak menambah uji konfirmatori atau mengklaim koreksi perbandingan berganda.
Lima tabel dan satu gambar tiga panel dibentuk otomatis. Semua 36 kombinasi
model/konfigurasi tercakup dalam lampiran; CSV juga memuat sensitivitas invalid.

Klaim numerik utama yang dicocokkan:

- MM→MB Qwen3: ΔTPR tambahan +7,29 poin, CI [1,02; 14,13]; ΔFPR +2,30 poin.
- MM→MB Phi: ΔTPR −11,46 poin, CI [−19,54; −4,08]; ΔFPR −5,46 poin.
- Pada estimasi titik keenam model, tidak ada MM→MB yang menurunkan FPR TYP
  sekaligus mempertahankan atau menaikkan TPR tambahan. Ini bukan pembuktian
  kemustahilan pada populasi lain.
- MB Qwen7B: 86/96 TP tambahan dan 919/1.868 FP awal; MB Qwen3: 46/96 TP dan
  104 FP. TPR tambahan dan FPR awal tidak diberi label sebagai cohort baru yang sama.
- Intent pada MB Qwen7B: ΔTPR +10,42 poin, CI [2,13; 19,05]; ΔFPR +3,53 poin.
- Qwen3 MB, invalid-as-malicious: TPR tambahan 47,92→52,08%; FPR 5,57→8,46%.
- Biaya di teks memakai cohort awal yang sama, bukan mencampur median dari
  cohort awal dan tambahan.

## Batas klaim

Deskripsi lama tentang anotasi ganda, gold evidence, FPR_HN konfirmatori, card
berbasis penalaran ahli, dan stabilitas multi-seed diganti dengan metode yang
benar-benar digunakan. Tidak mengubah label. Tidak menyatakan semua pendahulu
terbukti benign, semua target adalah takeover, atau metode mengungguli tool
yang tidak diuji pada data sama. Penjelasan mekanisme kesalahan tidak dibuat
dari alasan model saja. Tidak mengklaim artefak sudah dirilis publik.

Urutan perluasan model/data sesudah hasil awal diketahui dijelaskan. Naskah
mencantumkan keterbatasan pemotongan diff, fallback, source labels, clustering,
pretraining, satu seed, structured output, serta cache/urutan latensi.
Tidak menambahkan kewajiban anotasi manusia atau fine-tuning.

## Sumber eksternal yang diperiksa

- [Wyss et al.](https://ldklab.github.io/assets/papers/raid25-llmdetection.pdf):
  tugas pembaruan dan smart-diff; angka lintas dataset tidak dibandingkan langsung.
- [IntelGuard](https://arxiv.org/abs/2601.16458): contoh malicious dan penalaran
  laporan ancaman; berbeda dari card otomatis penelitian ini.
- [Benchmark Guo v2](https://arxiv.org/abs/2603.27549v2): kandidat dataset dan
  ambiguitas capability/intent. Tidak menebak venue final.
- [SocketAI](https://arxiv.org/abs/2403.12196) dan
  [taint slicing v3](https://arxiv.org/abs/2512.12313v3): konteks deteksi level paket.
- [Draz, halaman penerbit](https://doi.org/10.1038/s41598-026-71750-5): metadata
  bibliografi baru dicocokkan, volume 16, artikel 30912, tahun 2026. Artefak
  dipakai sebagai petunjuk; label target menggunakan pemeriksaan OSV.
- [Min et al.](https://aclanthology.org/2022.emnlp-main.759/): pengaruh demonstrasi
  tidak hanya label; tidak menyimpulkan card berlabel saja pasti gagal.
- [Zimmermann et al.](https://www.usenix.org/conference/usenixsecurity19/presentation/zimmerman):
  keterhubungan dan kepercayaan pada npm.
- RogueOne dan CHABADA mengikuti ledger sumber yang telah diperiksa di
  `docs/references.md`; halaman proyek RogueOne juga ditemukan pada situs penulis.

## Validasi dan batas kesiapan

Dua tes exporter lulus: invalid memengaruhi kedua jenis kesalahan sesuai
kebijakan, dan duplikasi tidak dapat menggantikan konfigurasi yang hilang.
Audit data aktual lulus. Sepuluh kunci sitasi tersedia dan build tidak memiliki
sitasi/referensi undefined. PDF sembilan halaman diperiksa visual pada
judul/abstrak, tabel utama, plot, dan lampiran. Tidak ada teks atau angka tabel
terpotong. Satu warning berasal dari kotak keyword nol-lebar template CAS;
warning tersebut tetap tercatat dalam log.

Backup naskah lama ada di `data/writing/paper-20261018/previous/`. File hasil
eksploratori dan file Inggris kosong dipertahankan. Belum commit. Metadata
penulis, deklarasi faktual, venue, serta akses artefak belum diisi. Audit semantik
kesalahan menyeluruh, stabilitas multi-seed, dan evaluasi temporal terkontrol
belum dilakukan; naskah menyatakannya sebagai keterbatasan.
