# Persiapan eksperimen berbasis dataset — 15 Oktober 2026

Desain aktif: [D99](source-labelled-final-20261014.md), dilanjutkan pemeriksaan
format D100. Tidak menunggu dua anotator. Label tetap disebut label sumber
atau assumed-benign; tidak ada gold manusia yang dibuat.

## Data yang benar-benar tersedia

Arsip Guo diindeks selektif di container tanpa jaringan. Keempat ZIP cocok
SHA-256 sebelumnya; seluruh 54 target ditemukan, salinan lintas arsip konsisten.
53 identitas paket berhasil diekstrak. `@solana/web3.js@1.95.7` gagal pemeriksaan
manifest unik dan dikeluarkan. Setelah pemeriksaan predecessor dan advisory,
43 pair berhasil direkonstruksi; 11 kandidat ditolak dengan alasan tersimpan.

Ke-43 label cocok dengan daftar sumber Guo. 86 pemeriksaan hash arsip dan tree
sebelum/sesudah cocok. Semua 11.902 pin kampanye yang diwarisi cocok dengan
audit sebelumnya. Material index juga cocok manifest audit D96. Arsip RogueOne
belum dipakai dalam kohort ini; tidak mengklaim seluruh D97 selesai.

Clustering incremental membandingkan seluruh materi baru terhadap fingerprint
lama dan sesama materi baru, dengan laporan MAL dan aturan hash D96 pada ambang
0,5. Penutupan klaster lama diwarisi, bukan dihitung ulang; ambang 0,8 belum
diulang. Hasil: 27.536 item, 7.212 klaster. Sepuluh MAL terpapar lewat identitas
atau kampanye dikeluarkan; tersisa **33 MAL dari 33 kampanye**.

| Bagian | Jumlah |
|---|---:|
| MAL sumber calon holdout | 33 |
| TYP popular | 692 |
| TYP random | 801 |
| TYP stream | 376 |
| Total calon input utama | 1.902 |
| KB malicious | 50 |
| KB assumed-benign | 25 |

TYP yang overlap dengan HN pending (108) tidak diberi label baru. Reservasi KB
menyingkirkan 25 TYP beserta nama/kampanyenya dari test; dua TYP tambahan terpapar
setelah penggabungan MAL baru. Jumlah di atas adalah cohort sebelum audit akhir
normalisasi/konteks dan pembekuan.

Normalisasi menghasilkan 1.901 pair sukses. Satu TYP stream,
`@libav.js/variant-vp9-opus@6.5.7`, timeout 300 detik pada kedua percobaan,
termasuk retry dengan memori lebih besar. Dicatat sebelum inferensi test dalam
`cohort/technical-exclusions.jsonl`; kandidat asli dan kedua kegagalan tetap
disimpan. Input yang dapat dirilis menjadi 33 MAL + 1.868 TYP (375 stream),
total 1.901. Ini attrition teknis, bukan koreksi label atau seleksi hasil model.

Dari 1.901 pair sukses, 96 diff terpotong, 38 pair memakai raw fallback pada
53 file, dan 135 pair tidak memiliki intent tersedia. Semuanya tetap masuk
audit konteks; keterbatasan input ini tidak disembunyikan atau dipilih ulang
berdasarkan prediksi. Ringkasan terikat hash output di
`cohort/normalization-summary.json`.

33 MAL masih di bawah minimum 40 rancangan lama; sesuai D99, hasil dibatasi
deskriptif, bukan pengujian hipotesis HN/recall noninferiority. Semua MAL ini
terbit 2016–2024, sebelum 6 November 2024 dan 5 Agustus 2025. Karena itu tidak
mendukung klaim generalisasi temporal setelah rilis model. Kampanye yang baru
untuk eksperimen tidak sama dengan contoh yang pasti tidak ada dalam pretraining.

## KB dan pemeriksaan

75 card memakai builder deterministik yang sama untuk dua label: deskripsi
verbatim, capability statis, kutipan dengan file/baris/hash, dan keterangan
bahwa rationale ahli tidak tersedia. Kutipan tidak mengklaim membuktikan label.
Seluruh card lolos provenance, batas 15 baris/512 token dan deskripsi 64 token
pada kedua tokenizer. 67 kandidat B ditolak: 65 tanpa lokasi capability dan
2 tanpa kutipan yang muat. Tidak ada kandidat M ditolak pada pemilihan akhir.

Preprocessing kini mempertahankan hash arsip dari manifest, menolak hash indeks
yang bertentangan, dan membawa provenance label/strata. Pembekuan akan memeriksa
semua dependency yang berubah dari package.json kedua versi; bukan hanya tiga
entry evidence yang dicatat extractor. MM/MB tetap harus memiliki komposisi,
anchor dan posisi yang sama; kedua arm MB memakai card identik.

## Uji dev sebelum test

Dev dipilih deterministik dari data yang sudah terpapar: lima MAL + lima TYP.
Tidak memakai calon holdout. Run awal seluruh 120 respons diverifikasi:
Qwen3 45/60 JSON valid (75%), Qwen2.5 47/60 (78,33%). Ini kegagalan format
terhadap ambang 90%, bukan hasil final kemampuan deteksi.

D100 menggunakan satu revisi instruksi format yang diizinkan §6.4. Semua
konfigurasi dan kedua model diuji ulang dalam direktori terpisah. Riwayat awal
di `data/evaluation/source-rag-20261015/`, revisi di
`data/evaluation/source-rag-v2-20261015/`. Dataset calon test dinormalisasi
offline secara terpisah; belum ada hasil test yang digunakan untuk menyetel
format, card, atau pemilihan model.

Dev D100 selesai: Qwen3 50/60 valid (83,33%), Qwen2.5 42/60 (70%). Keduanya
tetap gagal ambang 90%. D101 secara eksplisit mengubah kondisi inferensi ke
JSON Schema yang sama untuk semua arm/model, bukan revisi teks kedua. Dev
baru selesai di `data/evaluation/source-rag-v3-20261015/`: Qwen3 60/60 valid
(100%), Qwen2.5 59/60 (98,33%); seluruh 120 respons terverifikasi. Input dan hitungan
token prompt sama dengan D100; seluruh respons dihasilkan ulang. Dampak
constraint pada prediksi harus dilaporkan; validitas JSON bukan lagi ukuran
kemampuan format intrinsik model.

Satu invalid Qwen2.5 adalah respons `DIFF+I` pada scheduler dev yang mencapai
512 token (`finish_reason=length`). Tidak diulang atau dibuang: tetap invalid
dalam sensitivitas. Pemeriksaan kode: 24 tes terfokus lulus, ditambah uji
integrasi laporan dengan confusion matrix yang diketahui; selfcheck analisis
statistik lulus.

Percobaan teknis persiapan dipertahankan: dua penyusunan card dihentikan sebelum
hasil (pengetatan kutipan dan perbaikan penanganan ID sumber duplikat), satu
gagal pemeriksaan jumlah baris kutipan kosong di akhir. Audit token pertama
mendeteksi kekeliruan bentuk keluaran tokenizer (mapping, bukan daftar token);
percobaan itu dipisahkan dan audit yang benar menghitung hingga 29.800 token
prompt dev revisi. Tidak satu pun percobaan tersebut dipakai untuk inferensi
test. Regresi tercakup dalam test dan pemeriksaan artefak nyata.

## Pemantauan dan kelanjutan

`scripts/source-rag/status.sh` menampilkan normalisasi, hasil dev revisi,
status rilis test, dan cakupan per model. `./status.sh` lama tetap untuk D92,
yang tidak memuat MM/MB.

`pipeline/source_freeze.py` memeriksa provenance, pin, paparan, KB/test,
dependency dan budget sebelum menandai test dirilis. Setelah lolos, Stage 1
berisi **22.812 generasi** (1.901 × 6 × 2), di luar dev dan warm-up, apabila
seluruh input tersisa lolos audit konteks. Hasil
lengkap harus diverifikasi dari respons mentah sebelum ringkasan final dibuat.
Analisis sensitivitas/stabilitas Stage 2 belum dijalankan pada kohort ini.

**Rilis D101 berhasil pada 15 Oktober 2026:** 1.901 pair dan 75 card lolos
seluruh audit, `issues=[]`. Prompt maksimum kedua model 30.144 token ditambah
512 output, di bawah konteks 32.768. `protocol.json` menandai test dirilis;
snapshot dev tersimpan terpisah. Batch utama dijalankan lewat `run-final.sh`
di background, log `source-rag-v3-20261015/final.log`, PID di `final.pid`.
Status berjalan bukan hasil akhir TPR/akurasi.

Setelah test dirilis, `scripts/source-rag/run-final.sh` menjalankan seluruh
Stage 1 lalu membuat `results.md` dan `summary.json` menggunakan kode laporan
yang dibekukan. Kegagalan runner/verifikasi menghentikan rangkaian; laporan
final tidak dibuat dari matriks parsial. Perintah dapat dilanjutkan tanpa
mengulang respons yang sudah selesai.
