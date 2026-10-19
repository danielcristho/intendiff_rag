# Tambahan MAL dari sumber independen, 17 Oktober 2026

**Akuisisi dan preprocessing selesai: 96 calon pasangan MAL, 65 kampanye.**
Jumlah tersebut mencakup tiga pasangan/satu kampanye D103. Tambahan bersih
batch ini adalah **93 pasangan dan 64 kampanye**. Bersama test utama yang tetap
33 MAL/33 kampanye, tersedia 129 pasangan dari 98 kampanye menurut aturan
clustering yang berlaku. Ini cakupan data gabungan, **bukan hasil evaluasi baru**.

Test tambahan belum dirilis dan tidak ada inferensi baru. Prompt, model, KB,
dan test D101/D102 tidak diubah. Sasaran sekitar 100 kampanye tidak dijadikan
alasan melonggarkan aturan untuk menambah dua kampanye lagi.

## Sumber dan label

[Studi Draz, Scientific Reports](https://www.nature.com/articles/s41598-026-71750-5)
menyediakan identitas versi dalam [artefak Zenodo](https://zenodo.org/records/22057621).
Arsip artefak 429.595 byte sudah diunduh dan dicocokkan dengan checksum Zenodo;
kode/notebook penulis tidak dijalankan. Sumber lokal:
`data/upstream/draz-20261016/artifact.zip` dan `record.json`.

Tabel sumber dipakai sebagai petunjuk pencarian. Label target dikonfirmasi
secara terpisah melalui query versi tepat OSV yang mengembalikan ID `MAL-*`.
Delapan puluh dokumen advisory lengkap juga disimpan dan dipin; tidak ada
yang berstatus withdrawn pada pemeriksaan ini. Metadata registry menentukan
identitas, urutan publikasi, dan pendahulu menurut aturan semver lama.
Dua dari 96 pasangan memakai pendahulu berbeda dari yang diusulkan tabel sumber.

Pendahulu diperiksa terhadap sumber MAL yang sudah dimiliki dan advisory OSV.
**Tidak ditemukannya advisory bukan bukti gold benign**; label tetap berbasis
sumber, mengikuti D99. Data ini tidak membuktikan bahwa setiap paket pernah
diambil alih dari pengembang sah, dan label sumber dapat mencakup PoC atau
perilaku yang penilaiannya bergantung konteks. Tidak membuat gold manusia,
gold evidence, atau mengharuskan anotasi dua manusia.

## Alur penyaringan

| Tahap sumber Draz | Jumlah |
|---|---:|
| Record npm pada tabel sumber | 3.344 |
| Dikeluarkan karena nama sudah dimiliki/terpapar | 1.294 |
| Petunjuk versi yang diperiksa | 2.050 |
| Nama paket yang metadata registrynya diambil | 984 |
| Pasangan tersedia menurut metadata dan aturan pendahulu | 395 |
| Gugur: pendahulu memiliki advisory | 232 |
| Gugur: target tidak mendapat konfirmasi MAL OSV | 4 |
| Lolos pemeriksaan advisory | 159, dari 80 nama |
| Arsip berhasil diunduh dan cocok integrity | 317/318 |
| Pair lolos pemeriksaan arsip/identitas | 156 |

Pada tahap resolusi, 1.639 petunjuk tidak mempunyai metadata arsip target,
tiga tidak mempunyai urutan pendahulu yang dapat diverifikasi, dan 13 memiliki
pendahulu yang sudah tercatat malicious pada sumber yang dipegang.

Eksklusi teknis pada tahap arsip:

- `ori-poc@7.7.8`: manifest pendahulu tidak cocok dengan identitas yang diminta.
- `openprompt-lang@1.5.0`: kedua arsip melewati batas anggota/ukuran hasil ekstraksi.
- `codebuff-cli@1.1.10`: arsip pendahulu melewati batas unduhan 32 MiB.

156 pair baru digabung dengan empat pair D103 yang sudah lolos pemeriksaan
pendahulu. Empat tersebut mencakup tiga calon sebelumnya dan satu yang sudah
diketahui terhubung ke klaster lama; penyaringan kampanye tetap diulang pada
gabungan agar hubungan antarsumber tidak terlewat.

| Clustering gabungan | Jumlah |
|---|---:|
| Kandidat yang dikelompokkan | 160 |
| Terhubung ke pool historis, dikeluarkan | 31 |
| Melebihi batas tiga pair/kampanye, dikeluarkan | 33 |
| Calon holdout yang tersisa | **96 pair / 65 kampanye** |
| Tambahan bersih terhadap D103 | **93 pair / 64 kampanye** |

Closure D99 berisi 27.536 item diwariskan dan diverifikasi. Setiap fingerprint
baru dibandingkan dengan fingerprint seluruh pool lama dan kandidat baru lain;
advisory MAL serta hash file tambahan nontrivial tetap menjadi penghubung.
Seluruh nama/kampanye pool lama, exposure registry termasuk dependency, dan
nama/identitas test/dev/KB D101 diblok. Batas kemiripan 0,5 dan maksimum tiga
pair/kampanye tetap. Clustering ini proksi operasional kampanye, bukan atribusi aktor.

33 kampanye test utama tetap terpisah setelah perluasan closure; tidak ada
irisan dengan 65 kampanye calon tambahan. Distribusi ukuran kampanye tambahan:
46 kampanye berisi satu pair, tujuh berisi dua, dan 12 berisi tiga.

## Preprocessing dan audit

- **96/96 preprocessing sukses**, tanpa error pair.
- Dua file menggunakan raw fallback yang memang diperbolehkan normalizer:
  `66o@0.0.192/index.js` dan template `.ejs` pada `svharness@0.13.5`.
  Kode mentah dipertahankan; tidak diedit untuk memperbaiki hasil model.
- Delapan diff terpotong menurut budget smart-diff lama; flag `truncated` tetap ada.
- Semua hash source tree sebelum/sesudah preprocessing cocok. Intent tetap
  berasal dari versi sebelum update. Identitas, archive integrity, provenance
  label, pin kampanye, dan checksum artefak sumber diverifikasi ulang.
- Tahun publikasi calon tambahan: 2021=7, 2023=5, 2024=8, 2025=1, **2026=75**.
  Tanggal baru mendukung rencana evaluasi tambahan; belum membuktikan generalisasi.
- Ekstraksi, analisis teks, normalisasi, dan clustering dilakukan di container
  tanpa jaringan. Sampel tidak dipasang atau dieksekusi.
- Delapan tes ekspansi MAL lulus, termasuk empat tes baru untuk konfirmasi MAL,
  advisory pendahulu, pemeriksaan yang hilang, dan identitas versi advisory.

Audit pertama terhalang path absolut dependency yang dipin D103 tidak terpasang
di container. Mount read-only dengan path yang sama memperbaiki lingkungan;
tidak mengubah pin. Sebelum manifest terbit, satu pemanggilan preprocessing
tidak memproses item apa pun. Jalannya preprocessing yang lengkap kemudian
memproses seluruh 96 item, dan audit akhir memeriksa kesesuaian himpunan ID.

## Jalur lain yang diperiksa

- Guo: dari 1.781 kasus pendahulu hilang, sembilan bernama paket lama dan
  1.218 pendahulunya sendiri tercatat MAL pada sumber. Tersisa 554 petunjuk
  untuk 548 versi pendahulu unik. Hanya 84 versi lolos advisory; seluruh
  84 permintaan registry masih 404. **Tidak ada tambahan dari pemulihan ini.**
- Incident corpus: 164 manifest OSS pada commit
  `c3053ccc2a3eba2960b2f69e3f818383681e060e` diperiksa. Berkas kode lengkap
  tidak ikut disimpan sebagai arsip di tree repo. Beberapa record menunjuk
  payload parsial, rekonstruksi, atau endpoint privat; tidak diperlakukan
  sebagai arsip npm asli dan endpoint privat tidak diakses.
- Tiga petunjuk incident yang belum tercakup Draz diperiksa: flatmap-stream
  tidak mempunyai target/pendahulu yang tersedia; faker hanya mengembalikan
  GHSA, bukan konfirmasi MAL yang disyaratkan tahap ini; target
  react-native-international-phone-number tidak mendapat advisory MAL.
  Tidak ada label otomatis dari nama incident saja.
- MPAD-NPM menyediakan fitur/metadata; bukan arsip pasangan kode.
  [MalOSS](https://github.com/osssanitizer/maloss/blob/master/malware/README.md)
  menyimpan sampel pada repo privat dengan permintaan akses. Tidak ada
  permintaan akses atau pesan kepada pihak lain yang dikirim.

## Artefak dan penggunaan berikutnya

Root: `data/acquisition/mal-expansion-20261017/`.

- `draz/resolution-summary.json`, `download-summary.json`, `screen-summary.json`:
  penyusutan kandidat per tahap.
- `campaigns-with-exposure/split-proposal.jsonl` dan `new-links.jsonl`:
  keputusan per pair serta penghubung kampanye.
- `pairs.manifest.jsonl`: 96 calon dengan provenance, lokasi kedua versi,
  dan hash arsip/tree.
- `pairs.prepared.jsonl`: 96 hasil preprocessing kanonik, siap digunakan
  dalam persiapan evaluasi tambahan.
- `acquisition-verification.json`, `preparation-verification.json`:
  hasil audit beserta pin input/kode.

**Belum boleh menyebut 129 MAL sebagai test yang sudah dievaluasi.** Yang sudah
dievaluasi tetap 33 MAL; 96 lainnya calon evaluasi tambahan. Sebelum inferensi,
buat protokol/snapshot evaluasi terpisah dan audit konteks setiap konfigurasi
serta model. Jangan menambahkan file ini ke snapshot D101/D102 secara langsung.
