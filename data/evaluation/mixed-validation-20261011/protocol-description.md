# Protokol dev campuran D87 — 11 Oktober 2026

Kelanjutan D85 menguji apakah format ID bukti dan verifier tetap mendeteksi
kandidat malicious setelah menurunkan alarm pada HN. Pengguna menyetujui
kelanjutan eksperimen eksploratif; gold manusia tidak dibuat atau diasumsikan.

- Seluruh 32 kandidat MAL dari 32 kampanye yang dibekukan D86 digunakan tanpa
  seleksi ulang. Kelimanya LEGACY-I, SCHEMA-I, IDS-I, IDS-D, VERIFY-I: 160
  generasi nyata baru. Seluruh 160 hasil HN D85 digunakan kembali sebagai
  kontrol historis; bukan generasi baru atau FPR terverifikasi.
- Prompt, skema, parser, indeks evidence, dan runner D85 disalin identik.
  Qwen3-4B-Instruct-2507 revisi yang sama, BF16, temperature 0, seed 0, top_p 1,
  output 2.048, konteks 32.768, KV 6 GiB, satu sequence, prefix cache,
  generation-config=vllm. Tanpa warm-up generasi, retry otomatis, atau pemotongan
  tambahan. Error transport menghentikan batch; semua invalid disimpan.
- Audit lokal seluruh prompt sebelum inferensi menyisakan 4.096 token untuk
  tambahan verifier selain cadangan output. Prompt verifier aktual diverifikasi
  sebelum dikirim. Respons IDS-I menjadi hipotesis verifier untuk kedua verdict.
- Recall MAL hanya proxy label upstream, invalid dihitung benign dengan
  sensitivitas invalid-as-malicious. HN dilaporkan sebagai jumlah alarm saja.
  Laporkan semua arm, validitas, panjang keluaran, ID hilang/header/non-isi,
  transisi berpasangan per cohort, token, dan latency observasional.
- Perbandingan utama diagnosis: schema vs legacy untuk format; IDS-I vs schema
  untuk gabungan representasi/format/urutan field; IDS-I vs IDS-D untuk intent;
  VERIFY-I vs IDS-I untuk verifier. Faktor pada perbandingan representasi tidak
  diklaim terisolasi. Biaya metode verifier mencakup IDS-I dan panggilan kedua.
- Data pernah dilihat: MAL pada D81–D84, HN pada D85. Ini dev eksploratif,
  bukan holdout. Semua nama/hash/klon dan kampanye MAL terpilih tetap dikecualikan
  dari test/KB. HN belum dipetakan kampanye. Sesi/cache berbeda membatasi
  perbandingan latency antar-cohort. Tidak ada pengujian RAG atau H2/H3.
- Rekam versi lingkungan; periksa bobot, masukan, dan sumber sebelum/sesudah.
  Arsip dokumen keputusan sebelum D87 menjaga pin historis D86. Snapshot D85
  dan protokol D86 tidak diubah. `data/results.jsonl` tetap untuk studi utama.

Artefak: `data/evaluation/mixed-validation-20261011/`. Protokol JSON dibekukan
setelah audit konteks dan sebelum generasi pertama. Hasil ditulis terpisah dari
protokol ini; perubahan setelah pembekuan harus memiliki jejak amendemen.
