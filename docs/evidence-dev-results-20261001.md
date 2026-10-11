# Hasil D85: format, ID bukti, dan verifikasi ulang

**Selesai dan terverifikasi 1 Oktober 2026, 21:42 WIB/UTC+7: 160 inferensi
nyata Qwen3-4B pada 32 kandidat HN dev.** Semua request generasi HTTP 200,
tanpa pengulangan atau error transport. Ini hasil pengembangan pada input
belum berlabel gold, bukan evaluasi FPR/recall.

## Hasil lengkap

| Kondisi | JSON valid | Alarm malicious | Terpotong | Respons dengan ID tidak ditemukan |
|---|---:|---:|---:|---:|
| LEGACY-I: DIFF+I format lama | 29/32 (90,63%) | 5 | 0 | Tidak berlaku |
| SCHEMA-I: pesan sama + JSON schema | 32/32 (100%) | 6 | 0 | Tidak berlaku |
| IDS-I: ID baris + intent | 32/32 (100%) | 0 | 0 | 0 |
| IDS-D: ID baris tanpa intent | 32/32 (100%) | 0 | 0 | 0 |
| VERIFY-I: pemeriksaan ulang IDS-I | 32/32 (100%) | 0 | 0 | 0 |

Ketiga invalid LEGACY-I adalah kesalahan sintaks, bukan batas output:
`read-or-fetch@0.2.1`, `define-data-property@1.1.4`, `yallist@5.0.0`.
SCHEMA-I mempertahankan semua 29 verdict yang sebelumnya valid; tiga
invalid menjadi dua benign dan satu malicious. Kenaikan alarm 5 → 6
berasal dari keluaran yang sebelumnya tidak terbaca. Schema memperbaiki
format pada cohort ini, tidak membuktikan penalaran lebih benar.

SCHEMA-I → IDS-I mengubah enam malicious menjadi benign; 26 benign tetap.
IDS-D → IDS-I tidak mengubah satu pun verdict. IDS-I → VERIFY-I juga tidak
mengubah verdict: 32 benign tetap benign. Karena semua kandidat verifier
kebetulan benign, batch ini tidak menguji kemampuannya memperbaiki kandidat
malicious. Verifier memang dijalankan pada semua pair sesuai protokol.

**Nol alarm bukan FPR 0%.** Semua input masih kandidat HN pending dan tidak
ada cohort MAL berlabel independen pada batch ini. Hasil sama-sama cocok
dengan hipotesis berkurangnya tuduhan tanpa bukti maupun meningkatnya
kecenderungan selalu menjawab benign; recall belum dapat membedakan keduanya.

## ID ditemukan belum berarti bukti memadai

| Kondisi | Respons yang mengutip header/hunk | Respons tanpa satu pun baris isi |
|---|---:|---:|
| IDS-I | 11/32 | 4/32 |
| IDS-D | 7/32 | 1/32 |
| VERIFY-I | 9/32 | 3/32 |

Seluruh 266 ID dari ketiga kondisi ditemukan dalam diff dan tidak ada
duplikat dalam satu jawaban. Namun total 27 respons mengutip setidaknya satu
header/hunk; delapan hanya memiliki kutipan non-isi. Header/hunk yang
dimaksud adalah pembatas diff/nomor hunk, bukan perubahan `package.json`
yang tetap dapat menjadi bukti substantif. Tidak dilakukan relabeling
otomatis berdasarkan jenis kutipan.

Pembacaan deskriptif beberapa keluaran juga menunjukkan batas semantik:

- Pada `vue-pdf-dd`, SCHEMA-I menyebut dependency baru sebagai paket
  malicious yang dikenal; IDS-I dan VERIFY-I menyebutnya fork yang dikenal.
  Bukti yang dirujuk menunjukkan pergantian dependency, tidak memverifikasi
  reputasi salah satu klaim itu. Dua dari tiga ID juga menunjuk header hunk.
- Pada `travultr`, IDS-I dan verifier menyebut bagian username pada URL
  repositori sebagai personal token. Verifier mengubah penjelasan tentang
  penghapusan file, tetapi mempertahankan verdict dan salah satu kutipan
  berupa header file. ID yang nyata belum menjamin interpretasi tepat.

Ini contoh kesalahan penjelasan yang diperiksa dari keluaran/input, bukan
gold manusia atau estimasi prevalensi seluruh kesalahan semantik. Tidak
mengunjungi URL sampel atau menjalankan kode paket.

## Biaya yang terukur

| Kondisi | Token input + output | Median latency/pair | P95 latency/pair |
|---|---:|---:|---:|
| LEGACY-I | 126.586 | 1.004 ms | 1.565 ms |
| SCHEMA-I | 126.643 | 839 ms | 1.164 ms |
| IDS-I | 202.355 | 975 ms | 2.247 ms |
| IDS-D | 183.003 | 921 ms | 2.203 ms |
| VERIFY-I saja | 212.441 | 947 ms | 1.362 ms |
| IDS-I + VERIFY-I, biaya metode dua tahap | 414.796 | 1.916 ms | 3.480 ms |

Total 833.206 prompt token dan 17.822 completion token. Metode dua tahap
memakai sekitar 2,05 kali token IDS-I sendiri tanpa perubahan verdict pada
cohort ini. ID baris menaikkan panjang input; prompt aktual terpanjang
24.934 token, seluruhnya muat dengan output 2.048 di konteks 32.768.
Latensi observasional dengan urutan tetap dan prefix cache, bukan estimasi
kausal kecepatan antar-metode. Verifier belum menunjukkan manfaat tambahan
pada verdict yang membenarkan pemakaian otomatis dari hasil batch ini saja.

## Pemulihan dan verifikasi

CUDA gagal sebelum generasi pada percobaan awal. Setelah pengguna
menyetujui restart WSL, probe 14:38:35 UTC berhasil: cuInit=0, PyTorch
mengenali RTX 5090, dan operasi tensor GPU lolos. Ini bukti pemulihan
setelah restart, bukan penetapan penyebab dasar crash sebelumnya.

Tidak ada revisi prompt/input/parameter setelah pembekuan. Verifikasi akhir
mencocokkan 14 hash sumber/input, dua hash sumber upstream, 13 hash berkas
model, 160 hash request yang direkonstruksi, semua token prompt aktual,
parsing respons mentah, dan audit kutipan. Log mencatat 160 generasi serta
empat pemeriksaan `/tokenize`, semuanya HTTP 200. Server berhenti setelah
batch; terdapat peringatan cleanup satu semaphore pada shutdown, tanpa
error transport. Log startup gagal tetap disimpan dan verifikasi awal
diarsipkan sebagai `verification.pre-run.json`.

## Implikasi untuk tahap berikutnya

1. Prioritaskan validasi pada dev campuran MAL dan HN dengan label manusia
   independen, terpisah dari holdout. Jangan memilih format hanya karena
   semua prediksi menjadi benign. Ukur recall bersama FPR dan invalid.
2. Uji pembatasan kutipan ke ID baris isi serta pemeriksaan kecocokan klaim
   terhadap kode sebagai intervensi baru yang dibekukan terpisah. Jangan
   mengubah hasil D85 atau menjadikan keberadaan ID sebagai gold.
3. Pertahankan ablation intent. Pada cohort ini menambah intent tidak
   mengubah verdict format ID; tidak ada bukti manfaat intent dari batch
   ini saja. ID, format, dan urutan field berubah bersama dibanding SCHEMA-I.
4. Card MB/MM memerlukan label/rationale terverifikasi. Dataset dan gold
   HN, pemisahan kampanye, serta G1/G2 belum selesai. Paket D85 dan klon
   terkait tetap dikecualikan dari test/KB final.

Artefak: [ringkasan](../data/evaluation/evidence-dev-20261001/summary.json),
[verifikasi akhir](../data/evaluation/evidence-dev-20261001/verification.json),
[biaya/diagnosis](../data/evaluation/evidence-dev-20261001/costs-and-diagnostics.json),
[transisi dan alasan](../data/evaluation/evidence-dev-20261001/paired-changes.jsonl),
[protokol](evidence-dev-20261001.md), dan
[anotasi tanpa prediksi](../data/evaluation/evidence-dev-20261001/ANNOTATION.md).
