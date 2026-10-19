# Hasil RAG berbasis label dataset

MAL memakai label sumber; TYP assumed-benign. Ini evaluasi deskriptif, bukan gold manusia atau pengujian hipotesis FPR_HN. Invalid dihitung benign pada hasil utama dan malicious pada sensitivitas. Akurasi merupakan akurasi cohort dengan rasio kelas ini, bukan estimasi populasi npm.

| Model | Konfigurasi | TPR MAL (95% Wilson) | Akurasi cohort | Balanced accuracy | Invalid |
|---|---|---|---|---|---|
| phi4_mini | DIFF | 36.36% [22.19%, 53.38%] | 82.11% | 59.64% | 16 |
| phi4_mini | DIFF+I | 51.52% [35.22%, 67.50%] | 85.53% | 68.83% | 10 |
| phi4_mini | DIFF+I+M | 78.79% [62.25%, 89.32%] | 59.18% | 68.81% | 21 |
| phi4_mini | DIFF+I+MM | 66.67% [49.61%, 80.25%] | 63.23% | 64.92% | 23 |
| phi4_mini | DIFF+I+MB | 66.67% [49.61%, 80.25%] | 68.60% | 67.65% | 14 |
| phi4_mini | DIFF+MB | 60.61% [43.68%, 75.32%] | 65.97% | 63.33% | 11 |

| Model | Konfigurasi | Strata TYP | FP / n | FPR (95% Wilson) |
|---|---|---|---|---|
| phi4_mini | DIFF | live-stream-unseen-names | 60 / 375 | 16.00% [12.64%, 20.05%] |
| phi4_mini | DIFF | popular | 125 / 692 | 18.06% [15.38%, 21.10%] |
| phi4_mini | DIFF | random | 134 / 801 | 16.73% [14.30%, 19.47%] |
| phi4_mini | DIFF+I | live-stream-unseen-names | 53 / 375 | 14.13% [10.97%, 18.02%] |
| phi4_mini | DIFF+I | popular | 87 / 692 | 12.57% [10.31%, 15.25%] |
| phi4_mini | DIFF+I | random | 119 / 801 | 14.86% [12.56%, 17.49%] |
| phi4_mini | DIFF+I+M | live-stream-unseen-names | 144 / 375 | 38.40% [33.62%, 43.42%] |
| phi4_mini | DIFF+I+M | popular | 281 / 692 | 40.61% [37.01%, 44.31%] |
| phi4_mini | DIFF+I+M | random | 344 / 801 | 42.95% [39.56%, 46.40%] |
| phi4_mini | DIFF+I+MM | live-stream-unseen-names | 150 / 375 | 40.00% [35.17%, 45.04%] |
| phi4_mini | DIFF+I+MM | popular | 247 / 692 | 35.69% [32.21%, 39.33%] |
| phi4_mini | DIFF+I+MM | random | 291 / 801 | 36.33% [33.07%, 39.72%] |
| phi4_mini | DIFF+I+MB | live-stream-unseen-names | 120 / 375 | 32.00% [27.48%, 36.88%] |
| phi4_mini | DIFF+I+MB | popular | 221 / 692 | 31.94% [28.57%, 35.50%] |
| phi4_mini | DIFF+I+MB | random | 245 / 801 | 30.59% [27.49%, 33.86%] |
| phi4_mini | DIFF+MB | live-stream-unseen-names | 123 / 375 | 32.80% [28.24%, 37.71%] |
| phi4_mini | DIFF+MB | popular | 244 / 692 | 35.26% [31.79%, 38.89%] |
| phi4_mini | DIFF+MB | random | 267 / 801 | 33.33% [30.16%, 36.67%] |

Selisih paired dan CI bootstrap kampanye, sensitivitas invalid, serta token/latency tersimpan di `summary.json`. Tidak memilih konfigurasi atau mengubah prompt berdasarkan hasil test.
