# D90 — pembanding Granite pada seluruh kondisi D89

Pengguna meminta mencoba model baru untuk memperoleh keluaran pembanding.
Model dipilih sebelum prediksi: IBM Granite 3.3 8B Instruct, belum dijalankan
pada penelitian ini. Revisi resmi yang sudah diaudit D84 dipakai kembali:
`51dd4bc2ade4059a6bd87649d68aa11e4fb2529b`. Metadata/tokenizer tersedia lokal;
empat shard bobot diunduh dari repo resmi dan SHA-256 LFS diperiksa.

Pemilihan bukan karena hasil pada target ini. Ini pembanding keluarga lain dengan
ukuran lebih besar; perubahan tidak mengisolasi efek ukuran. Model card resmi:
https://huggingface.co/ibm-granite/granite-3.3-8b-instruct
Native template dipakai dengan `thinking=false`, bukan reasoning verbose.
Mode ini didukung template checkpoint; kontrol greedy bersama bukan klaim
setting benchmark optimal pengembang. Remote model code tidak dijalankan.

## Desain dibekukan sebelum inferensi

Seluruh 15 target D89 (14 HN pending + satu MAL sumber), dua arm NO-SOURCE dan
WITH-SOURCE, menghasilkan **30 inferensi baru**. Berkas pair, snapshot dependency,
prompt, schema, parser, urutan pair serta aturan pembalikan urutan arm identik.
Tidak memilih ulang target atau menyisipkan konteks baru setelah hasil D89.
Qwen3-4B D89 menjadi kontrol historis 30 respons, tidak dijalankan ulang.

BF16, seed 0, temperature 0, top_p 1, max_tokens 2.048, context 32.768,
KV 6 GiB, satu sequence, prefix caching dan generation-config vllm sama D89.
Tokenisasi berbeda alami antar model. Preflight seluruh 30 pesan Granite:
24.467 token maksimum, muat tanpa truncation baru atau perluasan konteks.
Request Granite menyertakan `chat_template_kwargs={thinking:false}` dan
`stop_token_ids=[0]`, sesuai EOS config resmi. Itu perbedaan native yang dicatat;
isi pesan penelitian tetap sama. Endpoint tokenize harus cocok sebelum generasi.

Tanpa warmup generasi, retry otomatis, repair JSON, atau perubahan parameter
berdasarkan prediksi. Invalid tetap disimpan. Log server, respons mentah,
request hash, token, kutipan, runtime, bobot dan sumber dipin/diaudit.

## Hasil yang akan dilaporkan

Jumlah malicious/benign/invalid per model/cohort/arm, transisi antar arm dan
antar model pada pair identik, validitas, unknown ID, kutipan isi dependency,
token dan latency observasional. Semua kombinasi dilaporkan termasuk negatif.
Tidak memilih model sampai angka naik. Lima belas target ini bukan benchmark
representatif; tidak membuat ranking umum atau signifikansi populasi.

Batas D89 tetap: semua HN hanya delta dependency_change, tidak ada snapshot
install hook, satu MAL belum gold, versi installed tidak diketahui, enam target
pernah masuk D86 dan semuanya dev terpapar. Alarm HN bukan FPR; lebih banyak
alarm bukan otomatis peningkatan deteksi. Tidak ada hasil RAG, gold manusia,
atau perbaikan penelitian utama yang dianggap terbukti. Studi MM vs MB serta
ablation intent tetap memerlukan card A/B terverifikasi dan split yang sah.
