# Hasil D88 — konteks dependency mengubah keputusan

Selesai 12 Oktober 2026, sekitar 00:31 UTC+7. **40 inferensi nyata** Qwen3-4B
selesai tanpa retry/error transport, tanpa menjalankan kode sampel. Seluruh 20
target berasal dari subgroup D87 yang menambahkan `easy-day-js`: diagnosis
post-hoc pada dev terpapar, dengan satu keluarga dependency bersama.

## Hasil dan interpretasi

| Kondisi IDS-I | Malicious | Benign | Invalid | Status |
|---|---:|---:|---:|---|
| Tanpa konteks dependency | 0/20 | 20/20 | 0 | Kontrol historis D87 |
| Konteks 1.11.21 | 0/20 | 20/20 | 0 | Inferensi baru, versi bersyarat |
| Konteks 1.11.22 | 20/20 | 0/20 | 0 | Inferensi baru, versi bersyarat |

Seluruh 20 keputusan beralih benign → malicious antara kedua snapshot. Tidak ada
respons terpotong atau unknown evidence ID. Instruksi kedua arm baru identik,
tetapi isi/panjang konteks berbeda. Terhadap kontrol historis, tambahan instruksi
kondisional juga berubah; efeknya tidak dipisahkan dari isi konteks.

Manifest 1.11.22 memuat `postinstall: node setup.cjs --no-warnings`; 1.11.21 tidak.
Pada pembacaan statis, setup memuat pengambilan konten jaringan, penulisan file,
dan pemanggilan proses anak, termasuk penonaktifan verifikasi TLS. Model merujuk
perilaku ini ketika memberi verdict malicious. Hasil mendukung diagnosis bahwa
**konteks dependency yang tidak terlihat pada diff target memengaruhi keputusan**.
Menambah ukuran model bukan satu-satunya arah perbaikan.

Kedua versi cocok `^1.11.21` dan terbit sebelum target menurut metadata arsip,
sementara lockfile tidak ditemukan. Karena versi instalasi aktual tidak diketahui,
**20/20 malicious bukan recall 100% atau kenaikan akurasi 100 poin**. Verdict
benign pada 1.11.21 juga bukan verifikasi keamanan seluruh tree. Dua puluh target
bukan dua puluh insiden independen; tidak dihitung p-value/CI insiden dari angka ini.

## Audit bukti dan biaya

Seluruh 40 request hash, token prompt, parsing respons mentah dan audit kutipan
cocok saat direkonstruksi. Sebanyak 21 checksum sumber, tiga kontrol historis,
serta 13 berkas model cocok; isi konteks cocok dengan berkas lokal/arsip.
Log mencatat 40 generasi HTTP 200 dan dua `/tokenize` HTTP 200. Server telah
berhenti. Empat pengujian terfokus dan selfcheck runner lulus.

Analisis kutipan berikut post-hoc, tidak mengubah verdict:

- Pada 1.11.22, 18/20 respons mengutip suatu ID konteks dependency, tetapi hanya
  **14/20 mengutip isi `setup.cjs`**. Enam lainnya tidak mengutip isi file itu.
  Ada 17 kutipan metadata/header konteks. ID yang ditemukan tidak menjamin
  bukti mendukung seluruh alasan.
- Pada 1.11.21, satu respons mengutip header konteks; tidak ada yang mengutip
  isi berkas dependency. Sebagian alasan menyatakan dependency sah karena
  fungsi tanggal sesuai intent; itu penilaian model, bukan verifikasi keamanan.
- Sejumlah alasan 1.11.22 menambahkan klaim eksfiltrasi, persistensi, atau
  kriptografi. Audit ini tidak memverifikasi klaim tambahan itu secara semantik.
  Verdict positif tidak otomatis berarti reasoning benar.

| Kondisi baru | Token prompt | Token output | Total token | Rasio terhadap IDS-I historis | Median latensi |
|---|---:|---:|---:|---:|---:|
| CTX-1.11.21 | 151.615 | 2.138 | 153.753 | 2,45× | 1.193 ms |
| CTX-1.11.22 | 214.175 | 2.236 | 216.411 | 3,45× | 1.346 ms |

Total baru 370.164 token; kontrol IDS-I untuk 20 target memakai 62.675 token.
Latensi hanya observasi sesi dengan prefix caching. Prompt maksimum 12.843 token;
semua masukan muat tanpa truncation tambahan. Tidak ada warmup LLM.

## Perlindungan validitas dan kelanjutan

Filter retrieval lama mengizinkan 40/40 kombinasi target dengan dua versi
dependency sebagai contoh KB karena nama/cluster berbeda. Filter baru menolak
40/40 menggunakan identitas dependency dalam metadata pair. Pengecualian nama
eksplisit juga didukung tanpa memakai intent. Aturan belum otomatis mencakup semua
dependency transitif, alias, perubahan versi registry, atau klon. Snapshot
eksperimen historis tetap dipertahankan.

Hasil ini layak ditulis sebagai **analisis eksploratif kecukupan konteks**, belum
sebagai keberhasilan hipotesis RAG atau solusi FPR. Tidak ada HN baru, card KB
berlabel, gold manusia, atau verifikasi instalasi dalam D88. Jangan mencampurnya
ke recall D87 atau tabel lintas model seolah kondisi sama.

Langkah penelitian berikut:

1. Siapkan kohort dependency dari beberapa keluarga/insiden, beserta HN dengan
   lifecycle/network/process yang sah. Tetapkan seleksi sebelum prediksi baru
   dan kelompokkan insiden berdasarkan dependency bersama.
2. Catat versi sebagai resolved-terverifikasi atau rentang ambigu. Untuk rentang
   ambigu, pisahkan hasil per versi; jangan memilih versi berdasarkan label atau
   verdict. Bekukan aturan pemilihan dan batas konteks.
3. Uji kontrol tanpa/dengan konteks dengan instruksi sejajar. Ukur trade-off recall
   sumber dan alarm HN; FPR memerlukan label benign terverifikasi. Nilai bukti
   trigger → tindakan → data/destinasi secara semantik, bukan ID saja.
4. Kembali ke **DIFF+I+MB vs DIFF+I+MM** serta **DIFF+I+MB vs DIFF+MB** setelah
   card A/B terverifikasi tersedia. Pakai input target sama di semua arm dan
   kecualikan target/dependency terkait dari contoh KB berlabel. D88 belum
   menetapkan konteks baru sebagai default studi utama.

Artefak: [protokol](dependency-context-20261011.md),
[ringkasan](../data/evaluation/dependency-context-20261011/summary.json),
[verifikasi](../data/evaluation/dependency-context-20261011/verification.json),
[diagnostik](../data/evaluation/dependency-context-20261011/diagnostics.json),
[respons mentah](../data/evaluation/dependency-context-20261011/results.jsonl).
