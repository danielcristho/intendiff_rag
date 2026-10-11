# Hasil validasi dev campuran D87 — 11 Oktober 2026

**160 inferensi MAL baru selesai dan terverifikasi pada Qwen3-4B.** Digabung
secara analitis dengan 160 respons HN historis D85, hasil ini menunjukkan bahwa
penurunan alarm dengan format ID disertai kehilangan deteksi terhadap label
sumber MAL. Intervensi ID/verifier belum layak dipilih sebagai perbaikan metode.

Ini eksperimen eksploratif nyata, bukan smoke test. Seluruh 32 MAL yang dipilih
D86 digunakan tanpa penggantian, lima arm per pair. Kontrol HN adalah seluruh
32 kandidat D85; tidak ada inferensi HN baru. Label MAL berasal dari upstream,
sedangkan label HN belum diverifikasi manusia. Recall berikut merupakan proxy
label sumber; jumlah alarm HN bukan FPR. Model, prompt, parser, dan anggaran
inferensi mengikuti [protokol](mixed-validation-20261011.md).

## Hasil seluruh kondisi

| Kondisi | MAL positif / 32 | Recall sumber | JSON valid MAL | Alarm HN historis / 32 | JSON valid HN |
|---|---:|---:|---:|---:|---:|
| LEGACY-I: DIFF+I format lama | 18 | 56,25% | 30/32 | 5 | 29/32 |
| SCHEMA-I: pesan sama, JSON schema | 19 | 59,38% | 30/32 | 6 | 32/32 |
| IDS-I: ID bukti + intent | 11 | 34,38% | 32/32 | 0 | 32/32 |
| IDS-D: ID bukti tanpa intent | 11 | 34,38% | 32/32 | 0 | 32/32 |
| VERIFY-I: pemeriksaan ulang IDS-I | 10 | 31,25% | 32/32 | 0 | 32/32 |

Invalid dihitung benign pada metrik utama. Dua invalid LEGACY-I gagal parsing
meski finish_reason=stop; dua invalid SCHEMA-I mencapai batas 2.048 token.
Jadi constrained decoding tidak menjamin objek lengkap jika anggaran keluaran
habis. Sensitivitas invalid-as-malicious memberi recall LEGACY-I 62,50% dan
SCHEMA-I 65,63%; tiga kondisi ID tidak berubah karena seluruh respons valid.

Perbandingan dilakukan berpasangan di cohort yang sama:

- **LEGACY-I → SCHEMA-I:** 18 malicious tetap, 11 benign tetap, dua invalid tetap,
  satu benign menjadi malicious. Perbaikan format pada HN D85 tidak berarti
  seluruh MAL otomatis valid atau benar.
- **SCHEMA-I → IDS-I:** delapan malicious menjadi benign; 11 malicious tetap,
  11 benign tetap, dan dua invalid menjadi benign. Penurunan recall sumber
  **25 poin** berasal dari perubahan verdict pada delapan respons yang sama-sama
  valid, bukan hilangnya deteksi akibat parser.
- **IDS-D → IDS-I:** seluruh verdict identik, 11 malicious dan 21 benign.
  Pada gabungan 64 dev, intent tidak mengubah verdict format ID. Ini tidak
  membuktikan intent tidak berguna secara umum atau pada konfigurasi RAG.
- **IDS-I → VERIFY-I:** satu malicious menjadi benign, 31 lainnya tetap.
  Tidak ada deteksi tambahan; alarm HN historis juga tetap nol.

Dibanding LEGACY-I, IDS-I turun 21,88 poin recall sumber. Hasil ini tidak
menjadi uji noninferiority konfirmatori, tetapi estimasi penurunannya jauh dari
sasaran menjaga recall dalam margin 5 poin. Model tidak selalu menjawab benign
pada seluruh MAL: ia masih mendeteksi 11/32. Namun nol alarm HN jelas bukan
alasan yang cukup untuk memilih intervensi ini.

## Diagnosis representasi dan dependency — analisis setelah melihat hasil

Pemeriksaan statis menemukan **20/32 kandidat MAL menambahkan `easy-day-js`**.
Delapan belas di antaranya hanya mengubah `package.json`; dua lainnya juga
mengubah log build. Nama dependency dicatat untuk diagnosis cohort ini, bukan
blacklist, fitur klasifikasi baru, atau label otomatis.

| Subgroup deskriptif | n | LEGACY-I positif | SCHEMA-I positif | IDS-I positif | IDS-D positif | VERIFY-I positif |
|---|---:|---:|---:|---:|---:|---:|
| Menambah dependency tersebut | 20 | 7 | 8 | 0 | 0 | 0 |
| Pair lainnya | 12 | 11 | 11 | 11 | 11 | 10 |

**Seluruh delapan deteksi yang hilang dari SCHEMA-I ke IDS-I berada pada
subgroup dependency ini.** Pada `@mastra/turbopuffer`, misalnya, IDS-I menyebut
penambahan dependency kemungkinan untuk tooling internal, tetapi alasan
tersebut tidak diverifikasi oleh kode dependency di smart-diff. Sebaliknya,
alasan SCHEMA-I bahwa dependency tidak terkait juga tidak cukup untuk membuktikan
malicious. Cocoknya verdict dengan label sumber tidak mengesahkan alasan model.

Temuan ini mengarahkan hipotesis berikutnya: update yang mengubah dependency
memerlukan konteks perilaku dependency yang relevan. Nama dependency di manifest
saja tidak membuktikan perilaku berbahaya maupun keamanan. Belum dapat ditetapkan
sebab tunggal: IDS-I sekaligus mengubah representasi diff, instruksi format,
dan urutan field dibanding SCHEMA-I. Jangan menyebut tabel post-hoc ini sebagai
bukti kausal efek ID baris atau hasil subgroup yang telah ditetapkan sebelumnya.

**Catatan clustering:** 32 MAL memiliki 32 ID klaster berbeda menurut pemetaan
yang tersedia, tetapi 20 di antaranya berbagi indikator dependency yang sama.
Itu tidak membuktikan satu insiden, sekaligus menunjukkan bahwa ID klaster
berbeda belum menjamin independensi kampanye. Pemetaan insiden/dependency perlu
diperiksa sebelum klaim 32 kampanye independen, bootstrap konfirmatori, atau
pemisahan KB/test. Seluruh hasil asli tetap dipertahankan.

## Verifier dan keterlacakan bukti

Satu perubahan verifier terjadi pada `@pkgr/core@0.2.8`. IDS-I mendeteksi
pemanggilan `rundll32` terhadap `node-gyp.dll`; verifier mengubahnya menjadi
benign dengan alasan fungsi diagnostik disk dan adanya logging/dry-run.
Baris D00156 memang mengeksekusi `child_process.spawn("rundll32", ...)`,
sedangkan kutipan itu sendiri tidak membuktikan isi DLL hanya diagnostik atau
bahwa logging membuatnya aman. Nama fungsi `logDiskSpace` bukan verifikasi
perilaku DLL. Ini contoh alasan yang terlalu menerima narasi kode; pembacaan
statis tersebut tidak menggantikan gold manusia dan tidak menjalankan DLL.

Pada MAL, semua ID ditemukan, semua 96 respons ber-ID memiliki sedikitnya satu
baris isi, tetapi enam respons juga mengutip header/hunk (dua per kondisi).
Pada HN D85 terdapat 27 respons yang mengutip header/hunk, delapan di antaranya
hanya non-isi. Keterlacakan sintaks telah membaik; dukungan semantik belum
terjamin. Tidak ada relabeling otomatis berdasarkan jenis kutipan.

## Biaya dan pemeriksaan teknis

| Kondisi MAL baru | Token input + output | Median latency |
|---|---:|---:|
| LEGACY-I | 93.641 | 1.123 ms |
| SCHEMA-I | 95.806 | 1.049 ms |
| IDS-I | 112.288 | 841 ms |
| IDS-D | 93.174 | 783 ms |
| VERIFY-I saja | 122.113 | 880 ms |
| IDS-I + VERIFY-I | 234.401 | 1.706 ms |

Total baru **517.022 token**. Metode dua tahap memakai **2,09 kali** token
IDS-I tanpa tambahan deteksi di cohort ini. Latency observasional, urutan
request tetap dan prefix cache aktif; bukan klaim kausal percepatan.

- 160 generasi HTTP 200, empat pemeriksaan tokenisasi HTTP 200; tanpa retry atau
  error transport. Server berhenti normal setelah batch selesai sekitar
  **18:59 UTC+7, 11 Oktober 2026**.
- 16 hash sumber/input, lima upstream, 13 berkas model cocok sebelum/sesudah.
  Seluruh 160 payload direkonstruksi; hash request, token aktual, parsing raw,
  audit kutipan, dan metrik cocok. Label sumber dan input MAL juga dicocokkan
  dengan corpus historis. Tiga tes regresi khusus D87 lulus.
- Prompt aktual maksimum 12.159 token; tidak ada pemotongan input tambahan.
  Python dan paket runtime sama dengan lingkungan D85.
- Snapshot D85, hasil HN, gold pending, dan label sumber tidak diubah. Tidak
  menulis hasil ke `data/results.jsonl`. Hasil MAL dan HN tidak digabung menjadi
  accuracy/F1 semu karena label HN belum tersedia.

## Implikasi untuk penelitian IntentDiff-RAG

**Pertahankan D87 sebagai hasil negatif intervensi, bukan konfigurasi pemenang.**
Verifier belum memberi manfaat yang membenarkan biaya tambahannya. Jangan
mengubah prompt di batch yang selesai untuk mengejar angka lebih tinggi.

Langkah berikutnya kembali ke gap utama penelitian:

1. Audit kecukupan input untuk perubahan dependency dan pemetaan insidennya.
   Jika konteks dependency ditambahkan, ambil isi versi yang relevan secara
   statis dan catat provenance; jangan memakai reputasi masa depan atau
   blacklist nama yang ditemukan dari hasil dev sebagai jawaban gold.
2. Siapkan pembanding malicious dan benign dengan pola dependency/lifecycle
   serupa dan alasan yang dapat diverifikasi. Uji **DIFF+I+MM versus DIFF+I+MB**
   dengan jumlah card sama, pengecualian paket/kampanye, dan input target sama.
   Ini menguji kontribusi utama, bukan sekadar membuat model lebih mudah benign.
3. Pertahankan ablation intent **DIFF+I+MB versus DIFF+MB** dan ukur deteksi MAL
   bersama alarm/FPR HN sesuai status label. Sebelum klaim konfirmatori,
   diperlukan gold independen dan split yang bebas dari paparan dev ini.

Analisis dependency di atas merupakan temuan untuk membentuk eksperimen baru,
bukan protokol baru yang sudah dijalankan. D87 sendiri tidak menguji retrieval,
perbaikan konteks dependency, atau efektivitas RAG.

Artefak di `data/evaluation/mixed-validation-20261011/`: `protocol.json`,
`results.jsonl`, `hn-historical-results.jsonl`, `summary.json`, `verification.json`,
`changed-verdicts.jsonl`, `source-label-misses.jsonl`, `citation-issues.jsonl`,
`costs-and-diagnostics.json`, dan `representation-strata.json`.
Skrip reproduksi verifikasi/analisis: `scratchpad/mixed-validation-20261011/`.
