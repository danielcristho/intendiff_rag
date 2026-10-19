# Evaluasi MAL tambahan D105

96 pair / 65 kampanye; label sumber, bukan gold manusia. Invalid dianggap benign pada hasil utama. Interval memakai bootstrap kampanye. FPR dan balanced accuracy tidak terdefinisi untuk cohort tambahan yang seluruhnya MAL. Hasil gabungan di summary.json hanya deskriptif dan memakai ulang TYP lama.

| Konfigurasi | TP / 96 | TPR baru (95% bootstrap kampanye) | Invalid |
|---|---|---|---|
| DIFF | 77 / 96 | 80.21% [71.58%, 87.91%] | 2 |
| DIFF+I | 84 / 96 | 87.50% [80.43%, 93.48%] | 4 |
| DIFF+I+M | 87 / 96 | 90.62% [84.78%, 95.79%] | 4 |
| DIFF+I+MM | 82 / 96 | 85.42% [78.49%, 91.67%] | 5 |
| DIFF+I+MB | 83 / 96 | 86.46% [79.07%, 93.02%] | 4 |
| DIFF+MB | 78 / 96 | 81.25% [72.83%, 88.42%] | 2 |
