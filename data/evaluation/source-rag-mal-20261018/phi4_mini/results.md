# Evaluasi MAL tambahan D105

96 pair / 65 kampanye; label sumber, bukan gold manusia. Invalid dianggap benign pada hasil utama. Interval memakai bootstrap kampanye. FPR dan balanced accuracy tidak terdefinisi untuk cohort tambahan yang seluruhnya MAL. Hasil gabungan di summary.json hanya deskriptif dan memakai ulang TYP lama.

| Konfigurasi | TP / 96 | TPR baru (95% bootstrap kampanye) | Invalid |
|---|---|---|---|
| DIFF | 45 / 96 | 46.88% [37.38%, 56.67%] | 2 |
| DIFF+I | 42 / 96 | 43.75% [33.68%, 54.74%] | 0 |
| DIFF+I+M | 57 / 96 | 59.38% [50.00%, 69.32%] | 2 |
| DIFF+I+MM | 60 / 96 | 62.50% [52.83%, 72.45%] | 3 |
| DIFF+I+MB | 49 / 96 | 51.04% [42.00%, 60.00%] | 3 |
| DIFF+MB | 55 / 96 | 57.29% [46.74%, 67.39%] | 2 |
