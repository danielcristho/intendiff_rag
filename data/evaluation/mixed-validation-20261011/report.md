# Hasil dev campuran D87

32 kandidat MAL berlabel sumber baru diuji; 32 kandidat HN memakai hasil historis D85.
Recall adalah proxy label sumber. Jumlah alarm HN bukan FPR.

| Arm | MAL positif / 32 | Recall sumber | Valid MAL | Alarm HN / 32 | Valid HN |
|---|---:|---:|---:|---:|---:|
| LEGACY-I | 18 | 56.25% | 30 | 5 | 29 |
| SCHEMA-I | 19 | 59.38% | 30 | 6 | 32 |
| IDS-I | 11 | 34.38% | 32 | 0 | 32 |
| IDS-D | 11 | 34.38% | 32 | 0 | 32 |
| VERIFY-I | 10 | 31.25% | 32 | 0 | 32 |

Invalid dipertahankan dan dihitung benign pada metrik utama; sensitivitas ada di summary.json.
Cohort kecil dan telah terpapar; tidak ada klaim gold, manfaat RAG, atau uji hipotesis utama.
