# Hasil D90 — Granite tidak mengubah keputusan pada kohort D89

Selesai **12 Oktober 2026, 05:44 UTC+7**. IBM Granite 3.3 8B Instruct
menyelesaikan **30 inferensi nyata** (15 target × dua kondisi). Seluruh hasil
dibandingkan dengan 30 respons historis Qwen3-4B D89 pada input yang sama.
Tidak ada verdict yang berubah. Ini hasil negatif yang tetap dilaporkan.

## Keputusan model

| Kohort | Kondisi | Target | Qwen malicious/benign/invalid | Granite malicious/benign/invalid |
|---|---|---:|---:|---:|
| HN pending | NO-SOURCE | 14 | 0/14/0 | 0/14/0 |
| HN pending | WITH-SOURCE | 14 | 0/14/0 | 0/14/0 |
| MAL sumber | NO-SOURCE | 1 | 0/1/0 | 0/1/0 |
| MAL sumber | WITH-SOURCE | 1 | 0/1/0 | 0/1/0 |

**Belum ada bukti kenaikan deteksi dengan model baru pada kohort ini.**
`zuper-cli@1.0.1`, satu-satunya MAL menurut sumber, tetap benign. Granite
menafsirkan dependensi umum dan setup Bun sebagai sesuai tujuan CLI. Ini
alasan model, bukan penilaian keamanan yang sudah diverifikasi manusia.
Label target juga tidak menetapkan `axios@1.6.8` sebagai dependency malicious.

Semua 30 respons JSON valid; nol output terpotong, unknown evidence ID, dan
error transport. Dua respons WITH-SOURCE mengutip isi dependency:
`get-symbol-description@1.0.2` dan `@tolicodes/picklejs@0.75.0`.
ID yang ditemukan tidak menjamin alasan benar secara semantik.

## Kendali eksperimen dan biaya

Seluruh input, snapshot, isi prompt, schema, parser, dan urutan sama D89.
BF16, temperature 0, top_p 1, seed 0, output 2.048, konteks 32.768, KV 6 GiB,
satu sequence dan prefix caching dipertahankan. Granite menggunakan template
native `thinking=false` dan EOS `[0]`. Maksimum prompt 24.467 token, tanpa
truncation tambahan. Tidak ada retry, repair JSON, atau warmup generasi.

Checkpoint `ibm-granite/granite-3.3-8b-instruct`, revisi
`51dd4bc2ade4059a6bd87649d68aa11e4fb2529b`; empat shard bobot dan berkas pendukung
diverifikasi sebelum protokol dibekukan. Pemilihan model dicatat sebelum
prediksi; tidak ada pemilihan ulang kondisi setelah hasil.

| Model | Kondisi | Token prompt + output | Median latensi HN |
|---|---|---:|---:|
| Qwen3-4B, historis | NO-SOURCE | 67.749 | 872 ms |
| Qwen3-4B, historis | WITH-SOURCE | 128.286 | 1.195 ms |
| Granite 3.3 8B, baru | NO-SOURCE | 76.964 | 1.676 ms |
| Granite 3.3 8B, baru | WITH-SOURCE | 146.418 | 2.422 ms |

Granite memakai total **223.382 token**, Qwen 196.035. Tokenizer berbeda;
jumlah token bukan pengukuran biaya komputasi lintas model. Latensi hanya
observasi sesi, dipengaruhi prefix caching dan tidak memakai warmup generasi.
Perbedaan keluarga, ukuran, tokenizer, dan template tidak mengisolasi efek ukuran.

Audit independen merekonstruksi semua request hash, token, urutan, parsing,
dan kutipan. **27 checksum sumber + enam artefak kontrol + 14 berkas model**
cocok. Log mencatat 30 generasi HTTP 200 dan dua tokenisasi HTTP 200; server
berhenti normal. Tiga pengujian terfokus lulus. Saat shutdown terdapat peringatan
pembersihan satu semaphore dari runtime, tanpa kegagalan generasi.

## Batas klaim dan penulisan

Kohort kecil dan terpapar dev: 14 HN belum gold, satu MAL hanya label sumber,
semua HN hanya sinyal dependency_change, nol snapshot memiliki install hook,
versi terpasang tidak diketahui. Nol alarm bukan FPR 0%; hasil ini juga tidak
menunjukkan kedua model setara secara umum. Eksperimen tidak menguji RAG
MM vs MB atau ablasi intent. Tidak ada kode sampel dieksekusi, card manusia
dibuat oleh model, atau hasil utama `data/results.jsonl` yang diisi.

Hasil D88–D90 sudah layak ditulis sebagai **analisis eksploratori**, termasuk
hasil negatif. Results dan Discussion ditambahkan melalui
`labs/latex/results-exploratory.tex` dan `labs/latex/discussion-exploratory.tex`
ke naskah utama `labs/latex/intendiff-rag.tex`. Kesimpulan utama penelitian
belum dapat ditulis sebagai hipotesis yang terbukti.

PDF draf 13 halaman berhasil dikompilasi dengan pdfLaTeX/BibTeX/latexmk,
tanpa referensi atau sitasi tak terdefinisi. PDF: `labs/latex/intendiff-rag.pdf`.
Peringatan tata letak pada bagian lama/daftar pustaka masih ada, dan metadata,
abstrak serta kesimpulan utama belum diisi. Petunjuk build ada di
`labs/latex/BUILD.md`. Perbaikan template terbatas pada opsi eksplisit abstract
kosong serta penghapusan deklarasi email kosong yang memicu ikon tidak tersedia.

Langkah berikut: memperluas sumber dependency relevan beserta HN runtime sah,
memastikan provenance/versi, dan menyelesaikan anotasi serta card A/B untuk
perbandingan MM vs MB. Menambah model saja belum mengatasi batas data ini.

Artefak: [protokol](granite-dependency-20261012.md),
[ringkasan](../data/evaluation/granite-dependency-20261012/summary.json),
[perbandingan](../data/evaluation/granite-dependency-20261012/comparison.json),
[verifikasi](../data/evaluation/granite-dependency-20261012/verification.json),
[respons mentah](../data/evaluation/granite-dependency-20261012/results.jsonl).
