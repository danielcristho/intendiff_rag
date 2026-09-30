# Pembanding model 3–4B versus 7–8B

Lengkap: 3.892 inferensi baru + 3.892 respons kontrol historis D82. Semua model memakai 973 pair yang sama, output 2.048 token, BF16, dan konteks 32.768. Label sumber; bukan evaluasi gold atau uji hipotesis konfirmatori.

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

Denominator per baris: 873 MAL, 100 TYP, dan 973 respons. Invalid dihitung benign; sensitivitas invalid-as-malicious dan biaya ada di comparison.json.

Qwen2.5-Coder dibandingkan dalam seri yang sama. Qwen3-4B-Instruct-2507 dan Qwen3-8B juga berbeda checkpoint/post-training, sehingga hasil tidak mengisolasi efek ukuran. Qwen3-8B memakai hard switch non-thinking; prompt dan parser dipertahankan.

Alokasi GPU 0,65 pada kontrol historis dan 0,80 pada model baru. Latency antar-sesi bukan estimasi kausal efek ukuran. Tidak ada gold manusia, HN, RAG, atau pembekuan G1/G2. Hasil tetap eksploratif; kelompok ukuran tidak mewakili seluruh populasi model.
