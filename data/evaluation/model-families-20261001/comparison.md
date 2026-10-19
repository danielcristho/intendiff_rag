# Pembanding enam model lokal: Qwen, Phi, dan Llama

Lengkap: 3.892 inferensi baru + 7.784 kontrol historis D82/D83. Semua memakai 973 pair yang sama, output 2.048 token, BF16, dan konteks 32.768. Label sumber; bukan evaluasi gold atau uji hipotesis konfirmatori.

| Model | Konfigurasi | Recall MAL sumber | FPR TYP | JSON valid | Terpotong | Macro recall kampanye |
|---|---|---:|---:|---:|---:|---:|
| Qwen2.5-Coder-3B-Instruct | DIFF | 84.54% | 48.00% | 86.84% | 75 | 78.69% |
| Qwen2.5-Coder-3B-Instruct | DIFF+I | 72.05% | 49.00% | 75.03% | 118 | 56.48% |
| Qwen3-4B-Instruct-2507 | DIFF | 54.98% | 6.00% | 71.74% | 7 | 42.38% |
| Qwen3-4B-Instruct-2507 | DIFF+I | 63.23% | 3.00% | 76.36% | 2 | 54.05% |
| Qwen2.5-Coder-7B-Instruct | DIFF | 92.90% | 65.00% | 94.04% | 3 | 93.05% |
| Qwen2.5-Coder-7B-Instruct | DIFF+I | 67.12% | 67.00% | 70.81% | 21 | 71.47% |
| Qwen3-8B | DIFF | 50.74% | 6.00% | 94.96% | 9 | 37.87% |
| Qwen3-8B | DIFF+I | 48.34% | 3.00% | 95.48% | 12 | 33.27% |
| Phi-4-mini-instruct | DIFF | 45.93% | 13.00% | 58.17% | 124 | 35.87% |
| Phi-4-mini-instruct | DIFF+I | 50.29% | 13.00% | 82.94% | 71 | 38.12% |
| Llama-3.1-8B-Instruct | DIFF | 85.45% | 57.00% | 88.08% | 2 | 76.44% |
| Llama-3.1-8B-Instruct | DIFF+I | 89.23% | 69.00% | 89.62% | 22 | 86.67% |

Denominator per baris: 873 MAL, 100 TYP, dan 973 respons. Invalid dihitung benign. Sensitivitas invalid-as-malicious, token, dan latency tersedia dalam comparison.json.

## Selisih terhadap setiap pembanding pada kelompok ukuran yang sama

| Model baru | Kontrol historis | Konfigurasi | Δ recall (poin) | Δ FPR (poin) |
|---|---|---|---:|---:|
| Phi-4-mini-instruct | Qwen2.5-Coder-3B-Instruct | DIFF | -38.60 | -35.00 |
| Phi-4-mini-instruct | Qwen2.5-Coder-3B-Instruct | DIFF+I | -21.76 | -36.00 |
| Phi-4-mini-instruct | Qwen3-4B-Instruct-2507 | DIFF | -9.05 | +7.00 |
| Phi-4-mini-instruct | Qwen3-4B-Instruct-2507 | DIFF+I | -12.94 | +10.00 |
| Llama-3.1-8B-Instruct | Qwen2.5-Coder-7B-Instruct | DIFF | -7.45 | -8.00 |
| Llama-3.1-8B-Instruct | Qwen2.5-Coder-7B-Instruct | DIFF+I | +22.11 | +2.00 |
| Llama-3.1-8B-Instruct | Qwen3-8B | DIFF | +34.71 | +51.00 |
| Llama-3.1-8B-Instruct | Qwen3-8B | DIFF+I | +40.89 | +66.00 |

Phi-4-mini dan Llama-3.1 menggunakan template serta stop token native resmi. Prompt, parser, sampling, dan input dipertahankan. Kontrol Qwen historis tidak memakai override stop_token_ids; ini tercatat sebagai perbedaan native lintas keluarga.

Kelompok A: 1≤P<5B; B: 5≤P<10B. Phi 3,836B dibandingkan dengan Qwen 3B/4B; Llama 8,030B dengan Qwen 7B/8B. Perbandingan tidak mengisolasi efek ukuran, post-training, data pelatihan, atau template chat.

Kontrol Qwen memakai alokasi otomatis 0,65 (3B/4B) atau 0,80 (7B/8B). Model baru memakai KV cache eksplisit 6 GiB setelah kegagalan startup tanpa prediksi; pengaturan eksplisit ini menggantikan perhitungan cache dari alokasi 0,80. Latency antar-sesi bersifat observasional. Gold manusia, HN, RAG, cutoff temporal formal, dan Gate G1/G2 belum selesai. Tidak ada pemotongan input tambahan atau pemilihan pair berdasarkan prediksi.
