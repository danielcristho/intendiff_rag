# Hasil penguatan dataset — 13 Oktober 2026

**Tahap akuisisi dan penyaringan otomatis selesai. Pool kini memuat 2.257
kandidat TYP dan 383 kandidat HN; 325 HN lolos pemeriksaan otomatis awal.**
Jumlah tersebut belum merupakan gold atau test set final. Evaluasi LLM lama
masih memakai kohort 973 pair; tambahan ini belum menjalani inferensi baru.

## Hasil utama

| Kelompok | Hasil aktual | Makna |
|---|---:|---|
| TYP popular | 902 pair | Asumsi benign, kedua versi tersedia dan pemeriksaan advisory bersih |
| TYP random | 974 pair | Asumsi yang sama; strata tetap dilaporkan terpisah |
| TYP stream, nama belum dipakai | 381 pair | Strata tambahan dari stream update yang diarsipkan Wyss |
| Total kandidat TYP | **2.257 pair** | Naik dari 100 pair yang dipakai evaluasi lama |
| HN jalur A lama | 182 kandidat; 162 lolos penyaringan awal | Pemeriksaan advisory diperbarui pada kandidat yang diterima |
| HN jalur B baru | **201 kandidat; 163 lolos penyaringan awal** | Publisher sama, advisory bersih, dan pemilihan pair tidak terhalang versi sebelumnya |
| Total kandidat HN | **383 kandidat; 325 lolos penyaringan awal** | Tujuan sah dan kategori masih perlu verifikasi manusia |
| MAL baru yang dapat dievaluasi | **0 pair** | Dua versi baru di manifest tidak tersedia sebagai arsip atau di registry |

Sebanyak **162 pair tumpang tindih** antara TYP dan HN yang lolos penyaringan.
Karena itu gabungan bahan review TYP/HN berisi **2.420 identitas pair unik**,
bukan 2.582. Tidak ada label gold manusia yang dibuat oleh pipeline.

## Cakupan akuisisi HN

Snapshot pencarian tetap menghasilkan 1.241 nama unik dalam batas 250 nama per
kategori. Metadata berhasil untuk 1.236 nama; lima mengembalikan HTTP 404.
Sebanyak 1.140 nama menghasilkan pasangan versi; 96 nama lainnya tidak
menghasilkan pasangan menurut aturan predecessor dan cutoff.

- Seluruh **17.225 versi yang direncanakan** memiliki status akhir: 17.097
  arsip berhasil diperoleh, total sekitar 9,80 GB; 128 gagal di tahap unduhan.
- Pemindaian berhasil untuk **16.922 versi**. Total 303 status gagal mencakup
  kegagalan unduhan serta batas ukuran/anggota arsip dan kecocokan identitas.
- Seluruh **16.018 pair** mempunyai hasil penyaringan; **15.715** memiliki
  kedua sisi yang dapat dipindai. Pair yang tidak tersedia tidak dianggap
  memiliki delta kosong.
- Dari 201 kandidat, 34 gagal karena publisher berubah/tidak diketahui,
  tiga karena pair sebelumnya tidak tersedia, dan satu karena advisory.
  Tersisa 163 kandidat untuk review tujuan perilaku.
- **91 dari 163** memiliki setidaknya satu sinyal network, process execution,
  install hook, dynamic code, atau obfuscation. Ini memperluas cakupan di luar
  perubahan dependency. Sebanyak 155 mempunyai berkas README/CHANGELOG/history;
  adanya berkas tersebut belum membuktikan tujuan sah.

| Kategori sinyal pada 163 kandidat baru | Pair |
|---|---:|
| Process execution/tooling | 53 |
| Telemetry/network | 31 |
| Licensing/dynamic code/obfuscation | 19 |
| Network/download/process | 50 |
| Perubahan struktur/dependency | 103 |

Kategori sinyal tumpang tindih dan **bukan kategori gold**. Angka kategori tidak
dijumlahkan. Batch awal 50 nama/kategori menghasilkan 33 kandidat; batch penuh
di atas sudah mencakup batch awal, sehingga keduanya juga tidak dijumlahkan.

## TYP dan independensi data

Dari 2.000 pair typical sumber, 1.883 lolos pemeriksaan arsip, identitas dan
advisory yang diarsipkan September. Pemeriksaan advisory baru menyisihkan tujuh
lagi, menyisakan 1.876. Sebanyak 117 sudah gugur pada audit awal; alasan dapat
tumpang tindih (95 advisory dan 23 ketersediaan/identitas).

Strata tambahan memakai `live_analysis_update_events.txt` dalam arsip replikasi
Wyss yang sama, berisi 1.122.663 baris. Setelah nama yang sudah ada pada pool
penelitian dikeluarkan, ada 260.175 nama yang memenuhi kriteria sampling.
Dipilih 500 nama dengan seed 2026, satu target versi berurutan hash per nama,
sebelum mengambil metadata atau melihat hasil penyaringan.

Sebanyak 387 pair dapat direkonstruksi: 90 pilihan tidak mempunyai predecessor
dengan urutan publikasi terverifikasi, 22 paket mengembalikan 404, dan satu
target versi tidak ada pada metadata. Enam pair kemudian gagal karena arsip
atau pemindaian; 381 diterima sebagai kandidat. Ada satu versi pendahulu yang
sempat masuk antrean sebelum target dinyatakan tidak tersedia; versi itu
tercatat dalam verifikasi dan tidak dihitung sebagai pair.

Pemilihan 500 nama berhasil direproduksi persis. Cohort stream ini bukan
sampel acak seluruh npm atau cohort pasca-rilis model. **FPR popular, random,
dan stream perlu dilaporkan terpisah**, atau digabung dengan bobot yang
ditetapkan sebelum inferensi.

Daftar paparan berbasis identitas/nama/dependency menyisakan **2.062 TYP** dan
**281 HN** dari bahan review yang belum terpapar menurut pemeriksaan tersebut.
Ini belum bukti bebas klon, kampanye terkait, atau kontaminasi pretraining.
Semua masih `holdout_eligible=false`, menunggu clustering dan split final.

## MAL dan keterbatasan yang belum terselesaikan

Snapshot Datadog `805fcd72db525244cae8dd32056efbd50b8b0e19` (9 Oktober 2026)
tidak menambah arsip compromised dibanding pool lama. Pemeriksaan manifest
menemukan dua tambahan, `@subql/common@5.8.3` dan `tensorlake@0.5.144`, tetapi
arsipnya tidak ada dalam subtree sumber dan endpoint versi tepat registry
mengembalikan 404. Keduanya dicatat sebagai petunjuk sumber, **bukan pair MAL
baru atau gold**.

MAL lama tetap 873 pair evaluasi dari 224 klaster; 607 berada dalam satu
klaster. Cap tiga pair per klaster memberi kapasitas 241 pair pada data itu,
tetapi seluruhnya tetap pernah terpapar pengembangan. Cap tidak menjadikan
data lama holdout baru. Akuisisi kampanye MAL baru masih diperlukan untuk
menguji generalisasi independen.

## Pemulihan dan verifikasi

Proses sempat berhenti; empat berkas terbuka ditemukan memiliki ekor byte nol.
Penyebabnya tidak diketahui. Salinan asli dan checksum disimpan dalam
`recovery-20261013/`. Hanya ekor nol setelah baris JSON utuh yang dibuang dari
dua manifest kerja; 4.266 catatan unduhan dan 4.576 catatan scan utuh dipertahankan.

Ada 324 cache arsip yang tidak cocok dengan digest. Berkasnya dipertahankan
dengan nama karantina, dan versi tepat diminta ulang. Seluruh **4.465 tree
hasil ekstraksi yang berhasil sebelum interupsi** tetap cocok dengan checksum.
Satu kegagalan unduhan lama dipindai ulang setelah arsip pulih dan cocok digest;
hasil sebelumnya disimpan. Seluruh kegagalan yang tersisa tetap masuk laporan.

Verifikasi akhir mencocokkan identitas seluruh rencana versi/pair dengan hasil,
hash metadata, hash arsip pada pemindaian, cakupan advisory, dan status label.
Delapan unit test terfokus lulus; pemeriksaan whitespace lulus. Tidak ada kode
package yang dijalankan, label manusia buatan, atau inferensi LLM tambahan.

## Kecukupan untuk penelitian

Pool benign kini lebih besar dan HN runtime lebih beragam. Itu belum menjamin
kelayakan jurnal Q1 atau power statistik. Sebagai sensitivitas analitis,
dengan asumsi pair independen dan ambang konservatif 0,05/6:

| Skenario hipotetis perbaikan / regresi keputusan | Efek bersih FPR | Power n=300 | Power n=500 |
|---|---:|---:|---:|
| 12% / 2% | −10 poin | 98,7% | >99,9% |
| 7,5% / 2,5% | −5 poin | 49,5% | 80,9% |
| 6,5% / 3,5% | −3 poin | 12,0% | 26,0% |

Ini **skenario, bukan efek hasil eksperimen**. Korelasi paket/kampanye dapat
mengurangi informasi efektif. Power non-inferiority recall belum dihitung.
Target 300–500 HN terverifikasi masih harus ditinjau dari efek yang ingin
dibuktikan; 325 yang lolos penyaringan otomatis belum berarti 325 gold HN.

Clustering gabungan dan usulan partisi sudah selesai (D96, [campaign-split-20261013.md](campaign-split-20261013.md)).
Pekerjaan berikutnya adalah anotasi A/B, pemeriksaan tujuan sah, normalisasi
smart-diff final/gold evidence, clustering gabungan dan pemisahan dev/test/KB,
serta penambahan MAL independen. Setelah itu baru bekukan matriks inferensi
dan jalankan eksperimen RAG/ablation. Panduan bahan review:
[dataset-expansion-review-20261013.md](dataset-expansion-review-20261013.md).

## Artefak dan reproduksi

- [Ringkasan gabungan](../data/acquisition/expansion-full-20261013/combined-readiness.json)
- [Ringkasan akuisisi HN penuh](../data/acquisition/expansion-full-20261013/summary.json)
- [Verifikasi strata stream](../data/acquisition/typical-stream-20261013/verification.json)
- [Sensitivitas power](../data/acquisition/expansion-full-20261013/power-sensitivity.json)
- [Protokol dan batas](dataset-expansion-20261012.md)

Rekonsiliasi hasil tersimpan, tanpa inferensi atau unduhan:

```bash
.venv/bin/python pipeline/expansion_report.py --out data/acquisition/expansion-full-20261013 --inventory data/acquisition/expansion-20261012
.venv/bin/python pipeline/typical_stream.py finish --out data/acquisition/typical-stream-20261013
.venv/bin/python pipeline/expansion_combine.py --out data/acquisition/expansion-full-20261013 --inventory data/acquisition/expansion-20261012 --stream data/acquisition/typical-stream-20261013
.venv/bin/python -m unittest tests.test_dataset_expansion -v
```
