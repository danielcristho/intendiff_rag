# Pembanding model lokal 3–4B dan 7–8B — D83

**Status: persiapan evaluasi; belum ada hasil baru 7–8B.**

Pengguna menyetujui tahap pertama dari [usulan model](model-scale-proposal-20260930.md).
Qwen2.5-Coder-7B-Instruct dan Qwen3-8B non-thinking dievaluasi pada seluruh
973 pair yang sama dengan D82: 873 MAL berlabel sumber dan 100 TYP yang
diasumsikan benign. Masing-masing memakai DIFF dan DIFF+I, sehingga ada
3.892 inferensi baru. Kontrol historis adalah 3.892 hasil D82 pada batas
keluaran yang sama, 2.048 token. Total perbandingan: 7.784 respons.

| Kelompok operasional | Checkpoint | Parameter total | Peran |
|---|---|---:|---|
| A: 1 ≤ P < 5B | Qwen2.5-Coder-3B-Instruct | 3,09B | Kontrol historis D82 |
| A: 1 ≤ P < 5B | Qwen3-4B-Instruct-2507 | 4,0B | Kontrol historis D82 |
| B: 5 ≤ P < 10B | Qwen2.5-Coder-7B-Instruct | 7,61B | Inferensi baru |
| B: 5 ≤ P < 10B | Qwen3-8B, non-thinking | 8,2B | Inferensi baru |

Batas kelompok ini dipakai untuk penyajian, bukan kategori baku atau
dasar untuk menggeneralisasi rata-rata kelompok ke semua model.

## Kontrol eksperimen

Input, prompt, parser, invalid-as-benign, BF16, seed 0, temperature 0,
top_p 1, konteks 32.768, dan output maksimum 2.048 dipertahankan dari D82.
Qwen3-8B menerima `chat_template_kwargs={"enable_thinking": false}`.
Tidak ada pemotongan input tambahan, pemanasan LLM sintetis, kuantisasi,
fine-tuning, atau pemilihan pair berdasarkan keluaran.

Model berjalan bergantian pada RTX 5090, `max_num_seqs=1` dan prefix
caching aktif. Alokasi GPU berubah dari 0,65 pada kontrol historis menjadi
0,80 untuk kedua model baru agar bobot/cache lebih besar muat. Latency
bersifat observasional antar-sesi. Perbandingan Qwen3 juga mencakup
perbedaan checkpoint/post-training; ukuran bukan satu-satunya faktor.

## Verifikasi dan keluaran

Snapshot berada di [direktori eksperimen](../data/evaluation/model-scale-20260930/).
Sebelum inferensi: pin revisi dan checksum bobot, audit tokenisasi 3.892
prompt, pembekuan protokol, pemeriksaan payload tanpa jaringan, dan dua
request `/tokenize` per model tanpa generasi.

Sesudah inferensi: pemeriksaan respons mentah dan parser, kelengkapan
973 pair pada setiap konfigurasi, token aktual versus audit, checksum
snapshot, serta jumlah request HTTP dalam log server. Laporan menyajikan
recall MAL sumber, FPR TYP, JSON valid, jenis invalid, sensitivitas
invalid-as-malicious, macro recall kampanye, transisi prediksi berpasangan,
token, dan latency. Seluruh kombinasi dilaporkan termasuk yang memburuk.

Ini evaluasi eksploratif setelah hasil awal diketahui. Belum ada gold
manusia, HN, evaluasi retrieval, atau uji hipotesis konfirmatori. G1/G2
belum selesai. Pemeriksaan cutoff rilis untuk analisis temporal formal
belum dilakukan terhadap model baru. RQ inti 3–4B dan enam konfigurasi
retrieval tidak otomatis diperluas oleh pembanding tambahan ini.

Rujukan model dan penelitian terkait: [usulan beserta sumber primer](model-scale-proposal-20260930.md).
Keputusan sebelum inferensi: [D83](decisions.md).
