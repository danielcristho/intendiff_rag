# Perbandingan RAG D101 dan tambahan D102

**Cakupan: 6/7 model selesai.** Model yang belum selesai tidak diisi dengan angka perkiraan.

Dua model utama selesai sebelum pemilihan lima model tambahan. Semua memakai 1.901 pair dan 75 card identik. MAL label sumber (33), TYP assumed-benign (1.868); akurasi cohort bukan estimasi populasi. Invalid dihitung benign pada tabel utama. Perbedaan tokenizer, chat template, konteks dan cache tercatat per model.

| Model | Konfigurasi | TPR MAL | FPR TYP | Akurasi cohort | Balanced accuracy | Invalid |
|---|---|---|---|---|---|---|
| qwen3 | DIFF | 39.39% | 6.37% | 92.69% | 66.51% | 144 |
| qwen3 | DIFF+I | 48.48% | 4.12% | 95.06% | 72.18% | 85 |
| qwen3 | DIFF+I+M | 51.52% | 4.82% | 94.42% | 73.35% | 69 |
| qwen3 | DIFF+I+MM | 45.45% | 3.27% | 95.84% | 71.09% | 58 |
| qwen3 | DIFF+I+MB | 57.58% | 5.57% | 93.79% | 76.00% | 57 |
| qwen3 | DIFF+MB | 45.45% | 7.92% | 91.27% | 68.77% | 85 |
| qwen25 | DIFF | 72.73% | 59.58% | 40.98% | 56.57% | 20 |
| qwen25 | DIFF+I | 78.79% | 59.31% | 41.35% | 59.74% | 18 |
| qwen25 | DIFF+I+M | 78.79% | 48.55% | 51.92% | 65.12% | 1 |
| qwen25 | DIFF+I+MM | 75.76% | 48.18% | 52.24% | 63.79% | 4 |
| qwen25 | DIFF+I+MB | 87.88% | 56.53% | 44.24% | 65.67% | 9 |
| qwen25 | DIFF+MB | 72.73% | 54.34% | 46.13% | 59.20% | 4 |
| qwen25_7b | DIFF | 78.79% | 65.15% | 35.61% | 56.82% | 6 |
| qwen25_7b | DIFF+I | 81.82% | 63.44% | 37.35% | 59.19% | 1 |
| qwen25_7b | DIFF+I+M | 87.88% | 46.79% | 53.81% | 70.55% | 3 |
| qwen25_7b | DIFF+I+MM | 81.82% | 45.18% | 55.29% | 68.32% | 3 |
| qwen25_7b | DIFF+I+MB | 81.82% | 49.20% | 51.34% | 66.31% | 4 |
| qwen25_7b | DIFF+MB | 69.70% | 45.66% | 54.60% | 62.02% | 5 |
| phi4_mini | DIFF | 36.36% | 17.08% | 82.11% | 59.64% | 16 |
| phi4_mini | DIFF+I | 51.52% | 13.87% | 85.53% | 68.83% | 10 |
| phi4_mini | DIFF+I+M | 78.79% | 41.17% | 59.18% | 68.81% | 21 |
| phi4_mini | DIFF+I+MM | 66.67% | 36.83% | 63.23% | 64.92% | 23 |
| phi4_mini | DIFF+I+MB | 66.67% | 31.37% | 68.60% | 67.65% | 14 |
| phi4_mini | DIFF+MB | 60.61% | 33.94% | 65.97% | 63.33% | 11 |
| llama31_8b | DIFF | 72.73% | 60.22% | 40.35% | 56.25% | 22 |
| llama31_8b | DIFF+I | 75.76% | 69.97% | 30.83% | 52.89% | 48 |
| llama31_8b | DIFF+I+M | 84.85% | 79.23% | 21.88% | 52.81% | 44 |
| llama31_8b | DIFF+I+MM | 72.73% | 68.58% | 32.14% | 52.08% | 55 |
| llama31_8b | DIFF+I+MB | 90.91% | 69.70% | 31.35% | 60.60% | 52 |
| llama31_8b | DIFF+MB | 72.73% | 57.71% | 42.82% | 57.51% | 31 |
| granite33_8b | DIFF | 42.42% | 10.06% | 89.11% | 66.18% | 104 |
| granite33_8b | DIFF+I | 48.48% | 7.71% | 91.53% | 70.39% | 93 |
| granite33_8b | DIFF+I+M | 48.48% | 8.83% | 90.43% | 69.83% | 95 |
| granite33_8b | DIFF+I+MM | 60.61% | 15.90% | 83.69% | 72.35% | 82 |
| granite33_8b | DIFF+I+MB | 60.61% | 15.79% | 83.80% | 72.41% | 72 |
| granite33_8b | DIFF+MB | 51.52% | 21.15% | 78.38% | 65.18% | 92 |

CI Wilson, FPR per strata, sensitivitas invalid dan perbandingan paired tersedia di results.md/summary.json tiap model. Tabel ini menggabungkan ringkasan yang sudah lolos verifier; tidak menggabungkan hasil D92 tanpa RAG.
