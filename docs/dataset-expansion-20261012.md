# Penguatan dataset — 12 Oktober 2026

Pengguna menyetujui penguatan dataset untuk target jurnal Q1. Target kerja
adalah 2.000–5.000 TYP, 300–500 HN terverifikasi, dan 200–400 MAL terverifikasi
dari kampanye beragam. Ini bukan syarat penerbitan atau ukuran sampel yang
telah dibuktikan cukup secara statistik. Jumlah akhir memerlukan analisis
power berpasangan, terutama untuk batas penurunan recall lima poin.

## Batch akuisisi pertama

1. Audit seluruh 2.000 pair TYP Wyss yang sudah ada, tanpa memilih berdasarkan
   capability atau prediksi. Laporkan semua kegagalan identitas/ketersediaan
   dan advisory. Kandidat yang juga masuk HN tetap ditandai; hasil dua subset
   tidak boleh dijumlahkan seolah independen.
2. Inventaris paparan memakai identitas pada input evaluasi baseline dan
   seluruh sidecar dev-exclusions. Nama paket dan dependency terkait ikut
   dikarantina untuk rencana holdout. Ketidakadaan dalam daftar paparan belum
   membuktikan bebas klon atau kontaminasi pretraining.
3. Jalur B memakai snapshot pencarian delapan kata kunci yang sudah diarsipkan
   pada September, dengan urutan SHA-256 nama paket, maksimum 250 per kategori.
   Ambil metadata registry untuk seluruh antrean itu. Batch bahan kode pertama
   mencakup **50 peringkat pertama per kategori**, bukan 50 kandidat yang lolos.
   Antrean peringkat 51–250 disimpan untuk batch berikutnya. Batas ini ditetapkan
   sebelum membaca hasil penyaringan, tidak diubah berdasarkan hasil model.
4. Gunakan 20 versi tertinggi menurut SemVer, sesuai implementasi `recent_pairs`
   yang sudah ada, dengan predecessor SemVer lebih rendah dan terbit lebih dulu.
   Versi setelah cutoff batch dikeluarkan. Ini bukan sampling temporal acak;
   prerelease tetap disertakan dan keterbatasannya dilaporkan.
5. Unduh versi tepat dari registry npm, periksa digest, lalu ekstrak/pindai
   statis di container tanpa jaringan. Tidak menjalankan package atau script.
   Batas operasional: tarball 32 MiB, total isi arsip 128 MiB, satu file 16 MiB,
   20.000 anggota per arsip; kasus melampaui batas dicatat sebagai tidak tersedia,
   tidak diam-diam dipotong. Batas tersebut dapat menghasilkan bias ukuran.
6. Per paket/kategori, ambil pair paling awal dalam urutan `recent_pairs` yang
   memiliki sinyal kategori. Jika pair sebelumnya tidak dapat dipindai, status
   pemilihan ditandai tidak lengkap. Gabungkan identitas yang sama antarkategori.
   Simpan semua pair yang dipindai, bukan hanya yang lolos.
7. Periksa advisory kedua versi dan identitas publisher pada kandidat.
   Kesamaan publisher atau ketiadaan advisory bukan label benign. Tujuan sah,
   kategori final, gold evidence dan card KB tetap memerlukan anotator A/B.

## Batas hasil dan split

Batch ini menghasilkan inventaris dan bahan review, bukan hasil inferensi
atau test set konfirmatori. Tidak mengubah dataset, prompt, atau hasil D92
yang sedang/selesai dijalankan. Sampel MAL lama seluruhnya telah terpapar;
cap kampanye hanya dipakai untuk mengukur kapasitas review, bukan menjadikannya
holdout baru. Akuisisi kampanye MAL baru dan cohort temporal merupakan pekerjaan
lanjutan yang harus dipisahkan dari sumber eksplorasi lama.

Split final dilakukan setelah anotasi dan clustering gabungan: pisahkan nama
paket, dependency terkait, klon, dan kampanye antara dev/test/KB. TYP baru dari
pool lama tidak otomatis merupakan holdout independen. Jangan membuang HN
dari TYP hanya supaya FPR turun. Untuk pelaporan, tampilkan tumpang tindih atau
gunakan rancangan subset terpisah yang dibekukan sebelum inferensi.

## Ukuran sampel

Dengan nol FP, batas atas Wilson 95% pada n=100/1.000/2.000 adalah sekitar
3,70%/0,38%/0,19%, dengan asumsi observasi independen. Pengulangan model/seed
tidak menambah n kasus independen. Power HN bergantung pada dua proporsi
perubahan keputusan yang berlawanan; ukuran MAL bergantung pada korelasi
kampanye dan discordance recall. Estimasikan kebutuhan memakai dev saja lalu
bekukan desain sebelum membuka hasil holdout.

## Kelanjutan antrean penuh — 13 Oktober 2026

Batch 1 menghasilkan 33 kandidat dari 3.192 pair yang dipindai. Akuisisi
dilanjutkan sampai batas sumber yang sudah ditetapkan: 250 peringkat per
kategori. Cutoff, snapshot pencarian, metadata berhasil, aturan sinyal dan
batas arsip tetap. Artefak kumulatif ada di
`data/acquisition/expansion-full-20261013/`; batch pertama tidak ditimpa.
Pemindaian versi batch pertama dipakai ulang dengan hash dan asal tercatat.
Jumlah hasil kumulatif tidak dijumlahkan dengan batch pertama. Tidak ada
perubahan kuota/sinyal berdasarkan verdict model, dan tidak ada inferensi baru.
