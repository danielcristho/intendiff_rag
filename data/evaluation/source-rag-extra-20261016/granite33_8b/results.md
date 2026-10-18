# Hasil RAG berbasis label dataset

MAL memakai label sumber; TYP assumed-benign. Ini evaluasi deskriptif, bukan gold manusia atau pengujian hipotesis FPR_HN. Invalid dihitung benign pada hasil utama dan malicious pada sensitivitas. Akurasi merupakan akurasi cohort dengan rasio kelas ini, bukan estimasi populasi npm.

| Model | Konfigurasi | TPR MAL (95% Wilson) | Akurasi cohort | Balanced accuracy | Invalid |
|---|---|---|---|---|---|
| granite33_8b | DIFF | 42.42% [27.24%, 59.19%] | 89.11% | 66.18% | 104 |
| granite33_8b | DIFF+I | 48.48% [32.50%, 64.78%] | 91.53% | 70.39% | 93 |
| granite33_8b | DIFF+I+M | 48.48% [32.50%, 64.78%] | 90.43% | 69.83% | 95 |
| granite33_8b | DIFF+I+MM | 60.61% [43.68%, 75.32%] | 83.69% | 72.35% | 82 |
| granite33_8b | DIFF+I+MB | 60.61% [43.68%, 75.32%] | 83.80% | 72.41% | 72 |
| granite33_8b | DIFF+MB | 51.52% [35.22%, 67.50%] | 78.38% | 65.18% | 92 |

| Model | Konfigurasi | Strata TYP | FP / n | FPR (95% Wilson) |
|---|---|---|---|---|
| granite33_8b | DIFF | live-stream-unseen-names | 34 / 375 | 9.07% [6.56%, 12.40%] |
| granite33_8b | DIFF | popular | 61 / 692 | 8.82% [6.92%, 11.16%] |
| granite33_8b | DIFF | random | 93 / 801 | 11.61% [9.57%, 14.01%] |
| granite33_8b | DIFF+I | live-stream-unseen-names | 34 / 375 | 9.07% [6.56%, 12.40%] |
| granite33_8b | DIFF+I | popular | 36 / 692 | 5.20% [3.78%, 7.12%] |
| granite33_8b | DIFF+I | random | 74 / 801 | 9.24% [7.42%, 11.44%] |
| granite33_8b | DIFF+I+M | live-stream-unseen-names | 42 / 375 | 11.20% [8.39%, 14.79%] |
| granite33_8b | DIFF+I+M | popular | 32 / 692 | 4.62% [3.29%, 6.46%] |
| granite33_8b | DIFF+I+M | random | 91 / 801 | 11.36% [9.35%, 13.75%] |
| granite33_8b | DIFF+I+MM | live-stream-unseen-names | 74 / 375 | 19.73% [16.02%, 24.06%] |
| granite33_8b | DIFF+I+MM | popular | 77 / 692 | 11.13% [9.00%, 13.69%] |
| granite33_8b | DIFF+I+MM | random | 146 / 801 | 18.23% [15.71%, 21.05%] |
| granite33_8b | DIFF+I+MB | live-stream-unseen-names | 72 / 375 | 19.20% [15.53%, 23.49%] |
| granite33_8b | DIFF+I+MB | popular | 80 / 692 | 11.56% [9.39%, 14.16%] |
| granite33_8b | DIFF+I+MB | random | 143 / 801 | 17.85% [15.36%, 20.66%] |
| granite33_8b | DIFF+MB | live-stream-unseen-names | 92 / 375 | 24.53% [20.45%, 29.13%] |
| granite33_8b | DIFF+MB | popular | 123 / 692 | 17.77% [15.11%, 20.80%] |
| granite33_8b | DIFF+MB | random | 180 / 801 | 22.47% [19.72%, 25.49%] |

Selisih paired dan CI bootstrap kampanye, sensitivitas invalid, serta token/latency tersimpan di `summary.json`. Tidak memilih konfigurasi atau mengubah prompt berdasarkan hasil test.
