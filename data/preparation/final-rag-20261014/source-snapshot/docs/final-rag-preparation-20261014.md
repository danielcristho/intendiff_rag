# Persiapan eksperimen akhir RAG — 14 Oktober 2026

Status: persiapan data dan pemeriksaan awal, **belum rilis inferensi final**.
Pengguna meminta fokus pada eksperimen akhir dan pencegahan kesalahan cakupan.
Hasil D92 tidak menggantikan eksperimen RAG.

## Cakupan utama yang berlaku

Metodologi §9–10 menetapkan Qwen3-4B-Instruct-2507 dan
Qwen2.5-Coder-3B-Instruct, enam konfigurasi:
DIFF, DIFF+I, DIFF+I+M, DIFF+I+MM, DIFF+I+MB, dan DIFF+MB.
Kontras konfirmatori: I versus I+M; I+MM versus I+MB; I+MB versus MB.
Stage 1 memakai seed 0, temperature 0, top_p 1 dan output 512 token.
Jumlah panggilan baru adalah N pair final × 6 konfigurasi × 2 model;
N belum dibekukan. Stage 2/EA2 tetap mengikuti metodologi dan harus
memiliki manifest sendiri sebelum inferensi.

Lima model tambahan D92 bukan otomatis model konfirmatori RAG. Pemilihan
model utama tidak diubah berdasarkan TPR D92. Prompt final belum
dibekukan; kode utama saat ini mengikuti §6 dengan evidence verbatim,
sedangkan ID/schema/verifier D92 adalah snapshot berbeda. Sebelum G2,
implementasi prompt yang dipakai harus dicatat eksplisit dan diuji pada dev;
jangan memasukkan verifier atau mengganti budget output di tengah run.

## Perbaikan yang sudah diterapkan

`pipeline/retrieval_audit.py` memeriksa seluruh pair/config sebelum runner
mengirim request atau menulis hasil. Runner menolak ID duplikat, metadata
nama/kampanye yang hilang, dan komposisi card yang kurang setelah filter.
MM harus mempunyai dua malicious; MB satu malicious dan satu benign.
Card malicious utama serta posisinya sama antara MM/MB, dan MB dengan/tanpa
intent harus mendapat card dalam urutan identik.

Fungsi retrieval tingkat rendah tetap dapat mengembalikan daftar pendek untuk
diagnosis. Runner batch kini menghentikan eksekusi ketika itu terjadi,
alih-alih mencatat konfigurasi MM/MB yang sesungguhnya kekurangan contoh.
Snapshot D92 dan hasil historis tidak diedit.

`pipeline/final_readiness.py` membuat laporan input dan rencana retrieval.
Periksa dengan:

```bash
.venv/bin/python pipeline/final_readiness.py \
  --out data/preparation/final-rag-20261014/readiness.json
```

Exit 2 berarti belum mendapat rilis final, bukan kegagalan transport model.
Tool ini **sengaja belum memberikan izin peluncuran**: validitas metadata
boolean tidak membuktikan anotasi manusia, provenance card, atau gate G1/G2.
Ia bukan pengganti validator rilis lengkap atau script inferensi final.
Default membaca `data/pairs.jsonl` dan `data/kb.jsonl` secara eksplisit;
tidak beralih ke fixture. Kedua file final belum tersedia saat audit.

## Bahan manusia dan dependensi rilis

250 kandidat HN D96 diproses menggunakan normalizer `static-dolos-exact-v2`
di container tanpa jaringan, sumber read-only, dua worker dan batas RAM 5 GiB.
Manifest tidak memuat label benign buatan. Log/keluaran/pin ada di
`data/preparation/final-rag-20261014/`. Tokenizer lokal Qwen2.5 dipakai untuk
budget smart-diff; audit prompt lengkap untuk kedua model masih diperlukan.
Normalisasi untuk anotasi tidak sama dengan pembekuan input inferensi final.

Hasil persiapan: 250/250 pair selesai, nol error pair; 250 hash diff dan
jumlah token cocok, serta 10 pin input/kode/tokenizer tetap cocok.
Sebanyak 53 diff terpotong, 15 pair mempunyai 74 file raw fallback, dan
intent tersedia pada 244/250 pair. Batas ini tetap ditampilkan kepada
anotator; nol kandidat dibuang untuk memperbaiki angka. Materi normalized
dan formulir A/B kosong ada di `annotation/`; flag review per pair ada di
`normalization-review-flags.jsonl`. Log `Timeout (0:01:00)` adalah diagnostic
faulthandler pada worker yang lama, bukan kegagalan pair; hasil semua pair
tetap direkonsiliasi dari output, bukan disimpulkan dari log progres.

Keempat ZIP Guo dan satu arsip RogueOne cocok ukuran dan MD5 metadata
Figshare; SHA-256 lokal dicatat di `external-archive-verification.json`.
D97 saat ini memiliki 54 kandidat pair Guo, 49 record predecessor dengan
47 ekstraksi sukses dan 2 error; 10 dari 49 pemeriksaan advisory positif.
Ini belum verifikasi v_t, provenance pair lengkap, atau MAL holdout baru.

Sepuluh unit test (6 pemeriksaan final/retrieval dan 4 regresi dependency)
lulus, begitu juga selfcheck runner/configs. Pengujian penolakan KB yang
kurang memastikan tidak ada request jaringan maupun file hasil yang dibuat.

Urutan penyelesaian yang diperlukan:

1. Selesaikan review sumber dan evidence oleh dua manusia independen untuk
   MAL/HN; simpan keputusan awal, kesepakatan, dan adjudikasi.
2. Selesaikan pair MAL D97 serta clustering gabungan terhadap pool terpapar.
   Arsip sumber yang berhasil diunduh bukan pair holdout atau gold.
3. Bagi HN test/KB menurut kategori; tulis card dalam bahasa Inggris oleh A,
   lalu periksa terhadap sumber oleh B. Terapkan kuota/cap metodologi.
4. Susun manifest test/KB final, gabungkan eksklusi dependency, dan audit
   ulang paparan identitas/nama/kampanye serta sumber/hash.
5. Audit isi card, batas 15 baris/512 token, konteks prompt kedua model,
   semua enam konfigurasi, dan kesamaan diff. Jalankan validasi dev yang
   ditetapkan, lalu bekukan G1/G2, model, kode, prompt, input, serta matriks.
6. Jalankan seluruh kombinasi baru dan cocokkan respons unik dengan manifest.
   Baru laporkan recall MAL, FPR HN/TYP, kontras MM–MB, CI/uji yang ditetapkan,
   invalid, biaya, dan cakupan yang belum selesai.

Hasil tidak dijamin bebas kesalahan oleh sebuah test. Pemeriksaan ini memberi
bukti yang bisa ditinjau dan menghentikan kasus kegagalan yang sudah diketahui;
ia tidak menggantikan label manusia atau audit semantik.
