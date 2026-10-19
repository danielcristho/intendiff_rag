# Evaluasi MAL tambahan D105

96 pair / 65 kampanye; label sumber, bukan gold manusia. Invalid dianggap benign pada hasil utama. Interval memakai bootstrap kampanye. FPR dan balanced accuracy tidak terdefinisi untuk cohort tambahan yang seluruhnya MAL. Hasil gabungan di summary.json hanya deskriptif dan memakai ulang TYP lama.

| Konfigurasi | TP / 96 | TPR baru (95% bootstrap kampanye) | Invalid |
|---|---|---|---|
| DIFF | 49 / 96 | 51.04% [39.58%, 62.65%] | 6 |
| DIFF+I | 42 / 96 | 43.75% [32.35%, 55.56%] | 7 |
| DIFF+I+M | 42 / 96 | 43.75% [32.38%, 55.32%] | 2 |
| DIFF+I+MM | 39 / 96 | 40.62% [30.00%, 51.52%] | 3 |
| DIFF+I+MB | 46 / 96 | 47.92% [36.84%, 59.09%] | 4 |
| DIFF+MB | 51 / 96 | 53.12% [41.75%, 64.95%] | 4 |
