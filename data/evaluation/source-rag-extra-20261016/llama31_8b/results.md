# Hasil RAG berbasis label dataset

MAL memakai label sumber; TYP assumed-benign. Ini evaluasi deskriptif, bukan gold manusia atau pengujian hipotesis FPR_HN. Invalid dihitung benign pada hasil utama dan malicious pada sensitivitas. Akurasi merupakan akurasi cohort dengan rasio kelas ini, bukan estimasi populasi npm.

| Model | Konfigurasi | TPR MAL (95% Wilson) | Akurasi cohort | Balanced accuracy | Invalid |
|---|---|---|---|---|---|
| llama31_8b | DIFF | 72.73% [55.78%, 84.93%] | 40.35% | 56.25% | 22 |
| llama31_8b | DIFF+I | 75.76% [58.98%, 87.17%] | 30.83% | 52.89% | 48 |
| llama31_8b | DIFF+I+M | 84.85% [69.08%, 93.35%] | 21.88% | 52.81% | 44 |
| llama31_8b | DIFF+I+MM | 72.73% [55.78%, 84.93%] | 32.14% | 52.08% | 55 |
| llama31_8b | DIFF+I+MB | 90.91% [76.43%, 96.86%] | 31.35% | 60.60% | 52 |
| llama31_8b | DIFF+MB | 72.73% [55.78%, 84.93%] | 42.82% | 57.51% | 31 |

| Model | Konfigurasi | Strata TYP | FP / n | FPR (95% Wilson) |
|---|---|---|---|---|
| llama31_8b | DIFF | live-stream-unseen-names | 206 / 375 | 54.93% [49.87%, 59.89%] |
| llama31_8b | DIFF | popular | 441 / 692 | 63.73% [60.08%, 67.23%] |
| llama31_8b | DIFF | random | 478 / 801 | 59.68% [56.24%, 63.02%] |
| llama31_8b | DIFF+I | live-stream-unseen-names | 237 / 375 | 63.20% [58.21%, 67.92%] |
| llama31_8b | DIFF+I | popular | 509 / 692 | 73.55% [70.15%, 76.70%] |
| llama31_8b | DIFF+I | random | 561 / 801 | 70.04% [66.78%, 73.11%] |
| llama31_8b | DIFF+I+M | live-stream-unseen-names | 279 / 375 | 74.40% [69.75%, 78.55%] |
| llama31_8b | DIFF+I+M | popular | 564 / 692 | 81.50% [78.44%, 84.22%] |
| llama31_8b | DIFF+I+M | random | 637 / 801 | 79.53% [76.59%, 82.18%] |
| llama31_8b | DIFF+I+MM | live-stream-unseen-names | 236 / 375 | 62.93% [57.94%, 67.67%] |
| llama31_8b | DIFF+I+MM | popular | 501 / 692 | 72.40% [68.95%, 75.60%] |
| llama31_8b | DIFF+I+MM | random | 544 / 801 | 67.92% [64.60%, 71.06%] |
| llama31_8b | DIFF+I+MB | live-stream-unseen-names | 238 / 375 | 63.47% [58.48%, 68.18%] |
| llama31_8b | DIFF+I+MB | popular | 497 / 692 | 71.82% [68.36%, 75.05%] |
| llama31_8b | DIFF+I+MB | random | 567 / 801 | 70.79% [67.54%, 73.83%] |
| llama31_8b | DIFF+MB | live-stream-unseen-names | 207 / 375 | 55.20% [50.14%, 60.16%] |
| llama31_8b | DIFF+MB | popular | 414 / 692 | 59.83% [56.13%, 63.42%] |
| llama31_8b | DIFF+MB | random | 457 / 801 | 57.05% [53.60%, 60.44%] |

Selisih paired dan CI bootstrap kampanye, sensitivitas invalid, serta token/latency tersimpan di `summary.json`. Tidak memilih konfigurasi atau mengubah prompt berdasarkan hasil test.
