# Evaluasi MAL tambahan D105

96 pair / 65 kampanye; label sumber, bukan gold manusia. Invalid dianggap benign pada hasil utama. Interval memakai bootstrap kampanye. FPR dan balanced accuracy tidak terdefinisi untuk cohort tambahan yang seluruhnya MAL. Hasil gabungan di summary.json hanya deskriptif dan memakai ulang TYP lama.

| Konfigurasi | TP / 96 | TPR baru (95% bootstrap kampanye) | Invalid |
|---|---|---|---|
| DIFF | 41 / 96 | 42.71% [31.37%, 54.17%] | 5 |
| DIFF+I | 29 / 96 | 30.21% [20.00%, 41.05%] | 2 |
| DIFF+I+M | 35 / 96 | 36.46% [24.30%, 49.47%] | 5 |
| DIFF+I+MM | 50 / 96 | 52.08% [40.21%, 63.81%] | 4 |
| DIFF+I+MB | 41 / 96 | 42.71% [31.37%, 54.35%] | 3 |
| DIFF+MB | 49 / 96 | 51.04% [39.18%, 63.00%] | 4 |
