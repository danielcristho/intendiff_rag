# Evaluasi MAL tambahan D105

96 pair / 65 kampanye; label sumber, bukan gold manusia. Invalid dianggap benign pada hasil utama. Interval memakai bootstrap kampanye. FPR dan balanced accuracy tidak terdefinisi untuk cohort tambahan yang seluruhnya MAL. Hasil gabungan di summary.json hanya deskriptif dan memakai ulang TYP lama.

| Konfigurasi | TP / 96 | TPR baru (95% bootstrap kampanye) | Invalid |
|---|---|---|---|
| DIFF | 74 / 96 | 77.08% [67.68%, 85.57%] | 0 |
| DIFF+I | 81 / 96 | 84.38% [76.92%, 91.01%] | 0 |
| DIFF+I+M | 75 / 96 | 78.12% [69.31%, 86.00%] | 0 |
| DIFF+I+MM | 79 / 96 | 82.29% [73.91%, 89.47%] | 0 |
| DIFF+I+MB | 79 / 96 | 82.29% [73.86%, 89.52%] | 0 |
| DIFF+MB | 77 / 96 | 80.21% [71.17%, 88.17%] | 0 |
