# Hasil RAG berbasis label dataset

MAL memakai label sumber; TYP assumed-benign. Ini evaluasi deskriptif, bukan gold manusia atau pengujian hipotesis FPR_HN. Invalid dihitung benign pada hasil utama dan malicious pada sensitivitas. Akurasi merupakan akurasi cohort dengan rasio kelas ini, bukan estimasi populasi npm.

| Model | Konfigurasi | TPR MAL (95% Wilson) | Akurasi cohort | Balanced accuracy | Invalid |
|---|---|---|---|---|---|
| qwen25_7b | DIFF | 78.79% [62.25%, 89.32%] | 35.61% | 56.82% | 6 |
| qwen25_7b | DIFF+I | 81.82% [65.61%, 91.39%] | 37.35% | 59.19% | 1 |
| qwen25_7b | DIFF+I+M | 87.88% [72.67%, 95.18%] | 53.81% | 70.55% | 3 |
| qwen25_7b | DIFF+I+MM | 81.82% [65.61%, 91.39%] | 55.29% | 68.32% | 3 |
| qwen25_7b | DIFF+I+MB | 81.82% [65.61%, 91.39%] | 51.34% | 66.31% | 4 |
| qwen25_7b | DIFF+MB | 69.70% [52.66%, 82.62%] | 54.60% | 62.02% | 5 |

| Model | Konfigurasi | Strata TYP | FP / n | FPR (95% Wilson) |
|---|---|---|---|---|
| qwen25_7b | DIFF | live-stream-unseen-names | 237 / 375 | 63.20% [58.21%, 67.92%] |
| qwen25_7b | DIFF | popular | 467 / 692 | 67.49% [63.91%, 70.87%] |
| qwen25_7b | DIFF | random | 513 / 801 | 64.04% [60.66%, 67.29%] |
| qwen25_7b | DIFF+I | live-stream-unseen-names | 211 / 375 | 56.27% [51.21%, 61.20%] |
| qwen25_7b | DIFF+I | popular | 478 / 692 | 69.08% [65.53%, 72.41%] |
| qwen25_7b | DIFF+I | random | 496 / 801 | 61.92% [58.51%, 65.22%] |
| qwen25_7b | DIFF+I+M | live-stream-unseen-names | 148 / 375 | 39.47% [34.65%, 44.50%] |
| qwen25_7b | DIFF+I+M | popular | 376 / 692 | 54.34% [50.61%, 58.01%] |
| qwen25_7b | DIFF+I+M | random | 350 / 801 | 43.70% [40.30%, 47.15%] |
| qwen25_7b | DIFF+I+MM | live-stream-unseen-names | 151 / 375 | 40.27% [35.43%, 45.30%] |
| qwen25_7b | DIFF+I+MM | popular | 354 / 692 | 51.16% [47.44%, 54.86%] |
| qwen25_7b | DIFF+I+MM | random | 339 / 801 | 42.32% [38.95%, 45.77%] |
| qwen25_7b | DIFF+I+MB | live-stream-unseen-names | 161 / 375 | 42.93% [38.02%, 47.99%] |
| qwen25_7b | DIFF+I+MB | popular | 375 / 692 | 54.19% [50.47%, 57.87%] |
| qwen25_7b | DIFF+I+MB | random | 383 / 801 | 47.82% [44.37%, 51.28%] |
| qwen25_7b | DIFF+MB | live-stream-unseen-names | 165 / 375 | 44.00% [39.06%, 49.06%] |
| qwen25_7b | DIFF+MB | popular | 318 / 692 | 45.95% [42.27%, 49.68%] |
| qwen25_7b | DIFF+MB | random | 370 / 801 | 46.19% [42.77%, 49.65%] |

Selisih paired dan CI bootstrap kampanye, sensitivitas invalid, serta token/latency tersimpan di `summary.json`. Tidak memilih konfigurasi atau mengubah prompt berdasarkan hasil test.
