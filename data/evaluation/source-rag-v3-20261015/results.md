# Hasil RAG berbasis label dataset

MAL memakai label sumber; TYP assumed-benign. Ini evaluasi deskriptif, bukan gold manusia atau pengujian hipotesis FPR_HN. Invalid dihitung benign pada hasil utama dan malicious pada sensitivitas. Akurasi merupakan akurasi cohort dengan rasio kelas ini, bukan estimasi populasi npm.

| Model | Konfigurasi | TPR MAL (95% Wilson) | Akurasi cohort | Balanced accuracy | Invalid |
|---|---|---|---|---|---|
| qwen3 | DIFF | 39.39% [24.68%, 56.32%] | 92.69% | 66.51% | 144 |
| qwen3 | DIFF+I | 48.48% [32.50%, 64.78%] | 95.06% | 72.18% | 85 |
| qwen3 | DIFF+I+M | 51.52% [35.22%, 67.50%] | 94.42% | 73.35% | 69 |
| qwen3 | DIFF+I+MM | 45.45% [29.84%, 62.01%] | 95.84% | 71.09% | 58 |
| qwen3 | DIFF+I+MB | 57.58% [40.81%, 72.76%] | 93.79% | 76.00% | 57 |
| qwen3 | DIFF+MB | 45.45% [29.84%, 62.01%] | 91.27% | 68.77% | 85 |
| qwen25 | DIFF | 72.73% [55.78%, 84.93%] | 40.98% | 56.57% | 20 |
| qwen25 | DIFF+I | 78.79% [62.25%, 89.32%] | 41.35% | 59.74% | 18 |
| qwen25 | DIFF+I+M | 78.79% [62.25%, 89.32%] | 51.92% | 65.12% | 1 |
| qwen25 | DIFF+I+MM | 75.76% [58.98%, 87.17%] | 52.24% | 63.79% | 4 |
| qwen25 | DIFF+I+MB | 87.88% [72.67%, 95.18%] | 44.24% | 65.67% | 9 |
| qwen25 | DIFF+MB | 72.73% [55.78%, 84.93%] | 46.13% | 59.20% | 4 |

| Model | Konfigurasi | Strata TYP | FP / n | FPR (95% Wilson) |
|---|---|---|---|---|
| qwen3 | DIFF | live-stream-unseen-names | 21 / 375 | 5.60% [3.69%, 8.41%] |
| qwen3 | DIFF | popular | 27 / 692 | 3.90% [2.70%, 5.62%] |
| qwen3 | DIFF | random | 71 / 801 | 8.86% [7.09%, 11.03%] |
| qwen3 | DIFF+I | live-stream-unseen-names | 14 / 375 | 3.73% [2.24%, 6.17%] |
| qwen3 | DIFF+I | popular | 17 / 692 | 2.46% [1.54%, 3.90%] |
| qwen3 | DIFF+I | random | 46 / 801 | 5.74% [4.33%, 7.58%] |
| qwen3 | DIFF+I+M | live-stream-unseen-names | 22 / 375 | 5.87% [3.91%, 8.72%] |
| qwen3 | DIFF+I+M | popular | 22 / 692 | 3.18% [2.11%, 4.77%] |
| qwen3 | DIFF+I+M | random | 46 / 801 | 5.74% [4.33%, 7.58%] |
| qwen3 | DIFF+I+MM | live-stream-unseen-names | 16 / 375 | 4.27% [2.64%, 6.82%] |
| qwen3 | DIFF+I+MM | popular | 14 / 692 | 2.02% [1.21%, 3.37%] |
| qwen3 | DIFF+I+MM | random | 31 / 801 | 3.87% [2.74%, 5.44%] |
| qwen3 | DIFF+I+MB | live-stream-unseen-names | 23 / 375 | 6.13% [4.12%, 9.03%] |
| qwen3 | DIFF+I+MB | popular | 25 / 692 | 3.61% [2.46%, 5.28%] |
| qwen3 | DIFF+I+MB | random | 56 / 801 | 6.99% [5.42%, 8.97%] |
| qwen3 | DIFF+MB | live-stream-unseen-names | 33 / 375 | 8.80% [6.33%, 12.10%] |
| qwen3 | DIFF+MB | popular | 36 / 692 | 5.20% [3.78%, 7.12%] |
| qwen3 | DIFF+MB | random | 79 / 801 | 9.86% [7.99%, 12.12%] |
| qwen25 | DIFF | live-stream-unseen-names | 210 / 375 | 56.00% [50.94%, 60.94%] |
| qwen25 | DIFF | popular | 433 / 692 | 62.57% [58.91%, 66.10%] |
| qwen25 | DIFF | random | 470 / 801 | 58.68% [55.23%, 62.04%] |
| qwen25 | DIFF+I | live-stream-unseen-names | 211 / 375 | 56.27% [51.21%, 61.20%] |
| qwen25 | DIFF+I | popular | 435 / 692 | 62.86% [59.20%, 66.38%] |
| qwen25 | DIFF+I | random | 462 / 801 | 57.68% [54.23%, 61.05%] |
| qwen25 | DIFF+I+M | live-stream-unseen-names | 184 / 375 | 49.07% [44.04%, 54.11%] |
| qwen25 | DIFF+I+M | popular | 344 / 692 | 49.71% [46.00%, 53.43%] |
| qwen25 | DIFF+I+M | random | 379 / 801 | 47.32% [43.88%, 50.78%] |
| qwen25 | DIFF+I+MM | live-stream-unseen-names | 176 / 375 | 46.93% [41.94%, 51.99%] |
| qwen25 | DIFF+I+MM | popular | 338 / 692 | 48.84% [45.14%, 52.56%] |
| qwen25 | DIFF+I+MM | random | 386 / 801 | 48.19% [44.75%, 51.65%] |
| qwen25 | DIFF+I+MB | live-stream-unseen-names | 198 / 375 | 52.80% [47.74%, 57.80%] |
| qwen25 | DIFF+I+MB | popular | 389 / 692 | 56.21% [52.49%, 59.87%] |
| qwen25 | DIFF+I+MB | random | 469 / 801 | 58.55% [55.11%, 61.91%] |
| qwen25 | DIFF+MB | live-stream-unseen-names | 194 / 375 | 51.73% [46.68%, 56.75%] |
| qwen25 | DIFF+MB | popular | 399 / 692 | 57.66% [53.95%, 61.29%] |
| qwen25 | DIFF+MB | random | 422 / 801 | 52.68% [49.22%, 56.12%] |

Selisih paired dan CI bootstrap kampanye, sensitivitas invalid, serta token/latency tersimpan di `summary.json`. Tidak memilih konfigurasi atau mengubah prompt berdasarkan hasil test.
