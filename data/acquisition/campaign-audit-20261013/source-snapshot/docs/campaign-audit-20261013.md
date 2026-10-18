# Audit penyebab klaster besar dan persiapan anotasi — 13 Oktober 2026

Audit ini melanjutkan D96. Tidak mengubah ambang, label, atau usulan split;
tidak menjalankan inferensi ataupun kode paket. Seluruh pembacaan sumber dan
fingerprint dilakukan di container tanpa jaringan.

## Penyebab penggabungan

Pada 27.493 item yang sama, kontribusi kriteria berbeda cukup besar:

| Kriteria yang dipakai | Jumlah klaster | Klaster terbesar |
|---|---:|---:|
| Laporan/advisory saja | 18.439 | 370 |
| Hash file D96 saja | 13.901 | 1.870 |
| Laporan + hash file D96 | 9.857 | 1.870 |
| D96 lengkap, termasuk Dolos ≥ 0,5 | 7.178 | 12.269 |

Klaster terbesar (`02-echo@0.0.7`) terdiri dari 11.581 item pool KB, 600
kandidat MAL, dan 88 kandidat review tambahan. Peran material review adalah
68 `review_typ` dan 20 `review_hn`; ini bukan label manusia dan tidak
memisahkan semua overlap TYP/HN. Sebelum tautan Dolos, anggota klaster ini
terbagi menjadi 1.996 komponen laporan/hash. Jadi, klaster raksasa bukan
semata-mata akibat satu hash file yang populer.

Ada perbedaan penting dalam material: pair menyumbangkan file yang baru
ditambahkan, sedangkan item KB tanpa versi pembanding menyumbangkan seluruh
file paket. Dolos memakai gabungan kode dengan suffix yang didukung extractor,
bukan hanya bagian yang telah diverifikasi sebagai payload. Karena itu,
kesamaan pustaka yang dibundel atau template juga dapat menjadi penghubung.
Ini konsekuensi representasi yang ada, bukan bukti asal serangan yang sama.

Pemeriksaan file menunjukkan bahwa aturan file identik masih menghubungkan
item melalui materi umum yang lebih panjang daripada batas D96:

- `public/next.svg`: hash yang sama pada 1.869 item.
- README template Next.js dan `next.config.mjs`: masing-masing pada 1.864 item.
- Stub `Object.defineProperty(exports, "__esModule", ...)` sepanjang 77 byte:
  pada 101 item di seluruh material.

Nama file dan contoh isi ini mendukung interpretasi bahwa sebagian tautan
mewakili kesamaan template/aset atau hasil kompilasi, bukan bukti tersendiri
bahwa semua anggota berasal dari satu insiden serangan. Tidak dilakukan
pelabelan otomatis atas asal kampanye. Pembatasan 64 byte saja belum
menghilangkan seluruh tautan semacam ini.

## Aturan dan batas interpretasi

Aturan D96 dipertahankan. Memisahkan klaster setelah melihat jumlah holdout
dapat mengubah estimasi independensi dan eksklusi KB. Audit ini tidak
memilih aturan baru untuk memperbesar test set. Jika definisi kampanye
direvisi, perlu bukti asal insiden/payload, keputusan desain tersendiri, dan
clustering serta split yang dihitung ulang sebelum pembekuan.

§3.6 metodologi diselaraskan dengan implementasi D96: yang diabaikan adalah
file dengan panjang di bawah 64 byte setelah `bytes.strip()`. Hanya whitespace
awal/akhir yang dibuang untuk uji panjang; whitespace tengah tetap dihitung,
dan SHA-256 tetap menggunakan isi mentah. Ini penjelasan aturan yang sudah
berjalan, bukan perubahan ambang.

## Paket anotasi

`data/acquisition/hn-annotation-20261013/` berisi 250 kandidat yang berstatus
`hn-pending-annotation` dalam usulan split, materi sumber sebelum/sesudah,
dan formulir A/B kosong. Urutan ditentukan hash identitas; tidak menggunakan
prediksi. Template 325 kandidat sebelumnya dipertahankan. Paket ini belum
memuat smart-diff final dan belum dapat dipakai untuk membuat evidence gold
berbasis diff atau menjalankan evaluasi.

Kategori sinyal, label sumber, dan hasil split tidak disalin ke materi
review. Identitas paket tetap terlihat dan konteks antrean menyatakan HN,
jadi tidak diklaim buta terhadap reputasi atau pemilihan kandidat.

Tiga calon holdout berbagi kampanye dengan 12 item KB. Daftar eksplisit ada
di `holdout-kb-exclusions.jsonl`; daftar ini harus diterapkan ketika menyusun
input retrieval final, belum diterapkan ke run historis.

Tetap belum ada MAL independen baru, label gold, card A/B terverifikasi, atau
test set beku. Usulan 274 dev, 1.896 TYP test-candidate, dan 250 HN pending
tetap berlaku.

## Verifikasi dan artefak

Artefak audit berada di `data/acquisition/campaign-audit-20261013/`:

- `witness-forest.jsonl`: 20.315 tautan cukup untuk merekonstruksi seluruh
  7.178 klaster pada 27.493 item. Terdiri dari 9.054 tautan laporan, 8.582
  hash file, dan 2.679 Dolos. Ini satu spanning forest yang valid, bukan
  seluruh edge graf atau atribusi sebab yang unik.
- `dev-exposure-paths.jsonl`: 79 jalur dari kandidat yang baru masuk dev ke
  endpoint yang teridentifikasi terpapar dari registry/peran/flag review.
  Sebanyak 36 jalur terpilih mengandung tautan Dolos; angka ini tidak berarti
  tidak mungkin ada jalur alternatif dengan kriteria lain.
- `hash-source-examples.jsonl`: 128 contoh file untuk 64 hash, dicocokkan
  kembali dengan isi file. Pemilihan mencakup 30 hash terpopuler dalam
  klaster terbesar, hash di jalur eksklusi, dan hash yang muncul pada review
  serta lebih dari 30 item di seluruh material. Ini pemilihan contoh
  diagnostik, bukan sampel acak estimasi proporsi boilerplate.
- `verification.json`: semua 11.912 pin input cocok; semua 20.315 tautan
  diperiksa ulang, termasuk menghitung skor Dolos dengan fungsi cache asli;
  79 jalur eksklusi valid; pemetaan klaster sama dengan snapshot D96.
- `tests.log`: 15 unit test lulus. Selfcheck `campaign.py` dan `runner.py`
  juga lulus. Tidak ada inferensi baru.

**Batas sertifikat:** audit membuktikan konektivitas di dalam klaster yang
sudah ada dan memeriksa seluruh tautan exact terhadap pemetaan itu. Audit
tidak mengulang seluruh perbandingan Dolos antar-klaster atau menghitung
ulang ambang 0,8. Fingerprint berasal dari cache yang cocok dengan hash
kode material; parsing Dolos seluruh korpus tidak dijalankan ulang.

Container: `intendiff-preprocess:campaign-v1`, image
`sha256:08d2f416af6e34f26c127cdb7dce786d1fe0840c1ee9f39303e8f0a87a5e82ec`.
Jaringan dimatikan, root filesystem read-only, capability dibuang, dan
output dibatasi ke direktori audit. Tiga percobaan audit awal dihentikan
untuk memperbaiki pemakaian memori/waktu; log disimpan sebagai
`audit-attempt1/2/3.log`. Material dan snapshot clustering tidak diubah.
Implementasi akhir memakai cache terbatas, indeks fingerprint, dan satu
perwakilan per kode identik; skor dan penutupan graf diverifikasi terpisah.

Reproduksi menggunakan `pipeline/campaign_audit.py` dengan kedua material
`full-d96.campaign-items.jsonl` dan `expansion.campaign-items.jsonl`, cache
`data/work/audit/fingerprints`, serta input split/review/exposure pada
`input-pins.jsonl`. Gunakan direktori output baru; jangan menimpa hasil ini.
Lanjutkan dengan `campaign_audit_evidence.py --audit DIR --review TYP HN`
dan `campaign_audit_verify.py --audit DIR` dalam container tanpa jaringan.
Antrean anotasi dibuat oleh `pipeline/expansion_annotation.py` dari review
HN gabungan dan usulan split D96; jangan menimpa formulir yang telah diisi.
