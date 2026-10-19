# D92 — evaluasi ulang penuh dengan diff ber-ID, schema dan verifier

Pengguna menegaskan bahwa perubahan kode harus diikuti evaluasi ulang, bukan
menyajikan angka baseline lama sebagai hasil implementasi terbaru. Batch ini
menjalankan inferensi baru pada **seluruh 973 pair** yang sudah digunakan
sebelumnya: 873 MAL label sumber dan 100 TYP diasumsikan benign. Semua tetap
dev terpapar, bukan holdout baru. Tidak mengambil subset HN/diagnostik.

## Implementasi dan matriks

Audit kode: `pipeline/prompts.py` masih format lama; perubahan filter retrieval
di runner tidak memengaruhi konfigurasi tanpa card. Implementasi diff ber-ID,
schema dan verifier berada pada snapshot D87, dan digunakan byte-identik dalam
batch ini. Studi versi dependency D88–D90 merupakan diagnosis bersyarat;
sumber/versi installed belum lengkap untuk seluruh dataset. Karena itu konteks
dependency tidak disisipkan secara tidak seragam ke batch utama ini.

Tujuh model: Qwen2.5-Coder-3B, Qwen3-4B-Instruct-2507, Qwen2.5-Coder-7B,
Qwen3-8B, Phi-4-mini, Llama-3.1-8B, dan Granite 3.3 8B. Bobot lokal/revisi
yang sama dengan eksperimen sebelumnya, checksum diverifikasi sebelum inferensi.

Per model, setiap pair menghasilkan tiga panggilan baru:

1. IDS-D: smart-diff ber-ID, tanpa intent, schema JSON ketat.
2. IDS-I: representasi sama ditambah intent versi sebelumnya.
3. VERIFY-I: verifier memeriksa seluruh kandidat IDS-I, benign maupun malicious;
   kandidat invalid diteruskan sebagai raw, tanpa perbaikan buatan.

Total **973 × 7 × 3 = 20.433 inferensi baru**. Tabel hasil membandingkan model
pada implementasi ini; tidak mengambil respons lama sebagai pengganti panggilan
baru. Biaya metode verifier mencakup IDS-I dan VERIFY-I. Tidak ada arm baseline
lama yang dijalankan dalam batch ini. Semua hasil, termasuk penurunan, dilaporkan.

## Panjang masukan dan kendali

ID baris menambah panjang prompt; audit seluruh pair × model dilakukan sebelum
prediksi. Konteks 32.768 dan output 2.048 dipertahankan. Prompt dasar dibatasi
26.624 token, menyisakan 4.096 untuk instruksi/candidate verifier. Jika perlu,
prefix baris diff dipotong **sekali per pair**, dengan budget yang muat pada
semua tokenizer dan kedua kondisi dasar. Prefix yang sama digunakan semua
model/kondisi, intent tidak dipotong ulang, tidak ada pair dihapus. Jumlah
pemotongan tambahan dan checksum sebelum/sesudah dicatat; ini berbeda dari
input baseline lama dan tidak disamarkan sebagai input identik secara byte.
Prompt verifier aktual juga diperiksa; bila melampaui konteks batch berhenti,
tidak melakukan truncation diam-diam atau melewati pair.

BF16, seed 0, temperature 0, top_p 1, max_tokens 2.048, KV 6 GiB, satu sequence,
prefix caching, generation-config vllm. Native EOS digunakan eksplisit untuk
semua model; Qwen3-8B enable_thinking=false, Granite thinking=false. Tidak ada
warmup generasi, retry otomatis, atau JSON repair. Data/sumber dianggap teks
tidak tepercaya dan tidak dieksekusi. Error transport tersimpan dan menghentikan
batch untuk audit. Proses melanjutkan respons unik yang sudah selesai, bukan
menghapus hasil invalid. Satu server milik eksperimen berjalan pada satu waktu.

## Pelaporan dan syarat lengkap

Per model/kondisi: deteksi pada MAL sumber, alarm salah pada TYP diasumsikan
benign, JSON valid, length-limited, ID tidak dikenal, sensitivitas invalid
sebagai malicious, token dan latensi observasional. Invalid dihitung benign
di metrik utama. Label bukan gold manusia; tidak ada klaim RAG MM vs MB,
FPR HN, atau signifikansi konfirmatori. Nama konfigurasi tampilan menyebut ID
dan verifier agar tidak tertukar dengan implementasi lama.

Model dinyatakan lengkap hanya jika seluruh 2.919 kombinasi unik tersedia,
semua request/token/parsing/kutipan direkonstruksi, hash input/model cocok,
dan log generasi/berhentinya server diperiksa. Ringkasan antar-model tetap
berstatus belum lengkap hingga seluruh tujuh model memenuhi syarat. Hasil
parsial tidak dipromosikan menjadi tabel lengkap paper. Arsip D81–D90 tidak
diubah. `data/results.jsonl` formal tetap terpisah.
