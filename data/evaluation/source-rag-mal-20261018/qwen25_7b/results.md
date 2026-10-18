# Evaluasi MAL tambahan D105

96 pair / 65 kampanye; label sumber, bukan gold manusia. Invalid dianggap benign pada hasil utama. Interval memakai bootstrap kampanye. FPR dan balanced accuracy tidak terdefinisi untuk cohort tambahan yang seluruhnya MAL. Hasil gabungan di summary.json hanya deskriptif dan memakai ulang TYP lama.

| Konfigurasi | TP / 96 | TPR baru (95% bootstrap kampanye) | Invalid |
|---|---|---|---|
| DIFF | 76 / 96 | 79.17% [70.00%, 87.23%] | 0 |
| DIFF+I | 83 / 96 | 86.46% [78.26%, 93.33%] | 0 |
| DIFF+I+M | 79 / 96 | 82.29% [74.49%, 89.47%] | 0 |
| DIFF+I+MM | 81 / 96 | 84.38% [76.77%, 91.21%] | 0 |
| DIFF+I+MB | 86 / 96 | 89.58% [82.95%, 95.19%] | 0 |
| DIFF+MB | 76 / 96 | 79.17% [70.71%, 87.10%] | 0 |
