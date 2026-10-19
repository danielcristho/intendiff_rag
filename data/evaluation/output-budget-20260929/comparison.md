# Eksperimen batas keluaran 512 → 2.048 token

Lengkap: 3.892 run baru dibandingkan dengan 3.892 run baseline historis. Semua empat kombinasi memakai 973 pair yang sama (873 MAL sumber + 100 TYP). Prompt, parser, model, dan parameter lainnya dipertahankan.

| Model | Konfigurasi | Recall sumber 512 → 2048 | FPR TYP 512 → 2048 | JSON valid 512 → 2048 | Terpotong 512 → 2048 |
|---|---|---:|---:|---:|---:|
| Qwen2.5-Coder-3B-Instruct | DIFF | 80.64% → 84.54% | 45.00% → 48.00% | 82.53% → 86.84% | 143 → 75 |
| Qwen2.5-Coder-3B-Instruct | DIFF+I | 68.16% → 72.05% | 43.00% → 49.00% | 70.81% → 75.03% | 234 → 118 |
| Qwen3-4B-Instruct-2507 | DIFF | 47.88% → 54.98% | 6.00% → 6.00% | 65.36% → 71.74% | 76 → 7 |
| Qwen3-4B-Instruct-2507 | DIFF+I | 56.70% → 63.23% | 3.00% → 3.00% | 70.61% → 76.36% | 67 → 2 |

Invalid tetap dihitung benign; analisis sensitivitas, macro recall kampanye, transisi valid/invalid/verdict, token, dan latency tersedia di `comparison.json`. Data ini sudah dipakai untuk menemukan masalah awal sehingga hasilnya eksploratif, bukan validasi pada holdout atau pembuktian hipotesis utama.

Kontrol 512 token berasal dari sesi sebelumnya, bukan run bersamaan. Versi perangkat lunak dan masukan dicocokkan. Kesamaan respons lengkap/prefix dicatat sebagai diagnosis reproduksibilitas; kesamaan tersebut tidak dipaksakan. Latency antar-sesi tidak cukup untuk klaim kausal atau benchmark RQ4.

Tidak ada evaluasi HN/retrieval, gold manusia, atau perubahan instruksi format. Korpus memiliki 224 klaster MAL; yang terbesar mencakup 607/873 pair.
