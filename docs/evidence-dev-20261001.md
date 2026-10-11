# Pengembangan verifikasi bukti — D85, 1 Oktober 2026

Status awal: implementasi/protokol dev, belum hasil akurasi baru. Pengguna
menyetujui kelanjutan diagnosis FPR. Tahap ini memakai update npm nyata.
Gold manusia dan card benign terverifikasi belum tersedia; tidak menghitung
FPR/recall dari kandidat HN pending atau membuat anotasi atas nama manusia.

## Cohort

32 kandidat HN dari review, diurut SHA-256 `D85-dev|id`, satu per nama paket,
hash diff, dan hash arsip versi. Nama/hash harus belum ada pada 973 pair
D82–D84; untruncated dan diff <=16.000 token berdasarkan preprocessing.
Batas panjang dev memberi ruang ID baris dan tahap kedua, tidak mengganti
pemotongan dataset utama. Cohort ini bukan sampel representatif populasi.

Clustering penuh yang tersedia mencakup MAL dan pool malicious KB, bukan HN.
Pemisahan paket/hash belum membuktikan bebas kemiripan kampanye.
`dev-exclusions.jsonl` mencatat paket dev untuk dikeluarkan dari test/KB
final; klon terkait juga perlu dikeluarkan setelah clustering HN. Sisa
kandidat belum dinyatakan holdout sah. Daftar review asli tidak diubah.
`annotation-input.jsonl` berisi input tanpa prediksi untuk dua anotator
independen, belum label gold. Ukuran 32 untuk pengembangan, bukan estimasi
FPR rendah atau generalisasi.

## Kondisi: 160 generasi nyata

| Arm | Input/format | Tujuan |
|---|---|---|
| LEGACY-I | DIFF+I historis, decoding biasa | Kontrol cohort baru |
| SCHEMA-I | Pesan sama persis LEGACY-I, JSON schema | Isolasi kendala decoder |
| IDS-I | DIFF+I, ID/jenis baris, verdict dahulu, JSON schema | Paket perubahan representasi bukti/format |
| IDS-D | Sama IDS-I tanpa intent | Ablasi intent |
| VERIFY-I | Input IDS-I dan kandidat jawaban IDS-I, panggilan baru | Pemeriksaan ulang klaim |

Verifier dijalankan pada semua kandidat termasuk benign dan invalid. Skema
sama dengan IDS-I; boleh mempertahankan atau mengubah kedua verdict. Ia
memeriksa bukti perilaku, perubahan added/deleted, pemicu, data/tujuan bila
relevan, dan penjelasan sah alternatif. Kandidat adalah hipotesis tidak
tepercaya. Ini pemeriksaan ulang model yang sama, bukan verifikasi semantik
deterministik atau anotasi independen.

Pemeriksa lokal memetakan ID ke baris/path/jenis/nomor sebelum-sesudah,
melaporkan ID tidak ditemukan, duplikat, dan kutipan tanpa baris isi.
Ia tidak mengubah verdict; ID valid tidak membuktikan alasan benar. Jenis
file bukan whitelist. IDS-I mengubah representasi, petunjuk format, dan
urutan field sekaligus; perbandingannya tidak mengisolasi ketiga komponen.

## Parameter, pembekuan, dan batas

Qwen3-4B-Instruct-2507 revisi D82, BF16, seed 0, temperature 0, top_p 1,
output 2.048, konteks 32.768, KV 6 GiB, max_num_seqs 1, prefix cache aktif,
generation-config vllm; tanpa warm-up sintetis. Tokenisasi semua tahap
pertama diaudit sebelum prediksi; `/tokenize` menguji kecocokan template.
Prompt verifier aktual diperiksa sebelum request, tanpa pemotongan tambahan.

Sumber, input, prompt, skema, tokenizer, bobot, script dibekukan sebelum
prediksi pertama. Invalid tetap disimpan tanpa repair. Error transport
menghentikan batch tanpa retry otomatis. Token prompt aktual harus cocok
dengan tokenisasi lokal. Controller menghentikan server yang dibuatnya.

Metrik: validitas JSON, length, keterlacakan ID, transisi verdict, token,
latency. Biaya VERIFY-I adalah IDS-I ditambah verifikasi. Urutan tetap dan
cache membatasi interpretasi latency. Alarm bukan FP; jumlah alarm turun
bukan bukti perbaikan deteksi. Tanpa gold, recall/FPR dan kebenaran semantik
belum diukur. Tidak ada perubahan enam konfigurasi utama, hasil historis,
atau G1/G2. MB/MM menunggu card dan label terverifikasi.

JSON schema menggunakan `response_format` yang didukung kode lokal dan
[dokumentasi vLLM](https://docs.vllm.ai/en/stable/examples/features/structured_outputs/).

## Reproduksi

1. `.venv/bin/python -m unittest discover -s tests -p 'test_evidence*.py' -v`
2. `.venv/bin/python data/evaluation/evidence-dev-20261001/prepare.py`
3. `.venv/bin/python -u data/evaluation/evidence-dev-20261001/evaluate.py`

Prepare menolak menimpa protokol beku. Checksum diperiksa sebelum dan setelah
run. Semua output tersimpan terpisah di `data/evaluation/evidence-dev-20261001/`.
