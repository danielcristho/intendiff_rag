# Evaluasi baseline data asli — 29 September 2026

**Eksploratif terhadap label sumber; bukan evaluasi gold atau hasil konfirmatori.**

Diperbarui: 2026-09-29T01:38:26.091951+00:00.

Run selesai: 2451/3892. Status lengkap: False.

Dataset: 873 MAL berlabel sumber + 100 TYP yang diasumsikan benign. Seluruh pair dipakai pada DIFF dan DIFF+I untuk kedua model, greedy/seed 0.

| Model | Konfigurasi | MAL ditandai malicious | FPR TYP | JSON valid | Median ms | p95 ms |
|---|---|---:|---:|---:|---:|---:|
| Qwen2.5-Coder-3B-Instruct | DIFF | 704/873 (80.64%) | 45/100 (45.00%) | 803/973 | 1084.3 | 3622.6 |
| Qwen2.5-Coder-3B-Instruct | DIFF+I | 595/873 (68.16%) | 43/100 (43.00%) | 689/973 | 1407.0 | 3656.2 |
| Qwen3-4B-Instruct-2507 | DIFF | 107/230 (46.52%) | 3/23 (13.04%) | 166/253 | 811.8 | 4070.9 |
| Qwen3-4B-Instruct-2507 | DIFF+I | 129/229 (56.33%) | 1/23 (4.35%) | 184/252 | 898.7 | 4110.6 |

Output tidak valid dihitung benign sesuai D18. Sensitivitas ketika output tidak valid dihitung malicious, macro recall per kampanye, dan token tersedia di `summary.json`. Error transport tidak dianggap prediksi.

Angka MAL mengukur kesesuaian terhadap label sumber, bukan recall terhadap anotasi manusia. Tidak ada evaluasi HN atau klaim manfaat RAG; card KB belum ditulis dan diverifikasi. Dataset ini belum memakai kuota dan cap kampanye test final. Perbedaan model/config dilaporkan apa adanya tanpa penyetelan prompt.

Latency mencakup request awal, dengan prefix caching aktif; angka ini bukan benchmark RQ4. Respons mentah, evidence, finish reason, token, dan latency setiap panggilan tersedia dalam `results.jsonl`. Model, revisi, parameter, dan checksum masukan tersedia dalam `protocol.json`.

MAL mencakup 224 klaster operasional; klaster terbesar memuat 607/873 pair. Macro recall memberi bobot yang sama pada tiap klaster dan tersedia di bawah. Angka ini tetap memakai label sumber dan definisi klaster §3.6, bukan validasi insiden independen.

| Model | Konfigurasi | Macro recall sumber per klaster |
|---|---|---:|
| Qwen2.5-Coder-3B-Instruct | DIFF | 76.66% |
| Qwen2.5-Coder-3B-Instruct | DIFF+I | 50.29% |
| Qwen3-4B-Instruct-2507 | DIFF | 35.61% |
| Qwen3-4B-Instruct-2507 | DIFF+I | 42.48% |

Diagnostik keluaran dan sensitivitas aturan invalid-as-malicious:

| Model | Konfigurasi | Batas 512 token | Invalid lainnya | MAL ditandai (sensitivitas) | FPR TYP (sensitivitas) |
|---|---|---:|---:|---:|---:|
| Qwen2.5-Coder-3B-Instruct | DIFF | 143 | 27 | 843/873 (96.56%) | 76/100 (76.00%) |
| Qwen2.5-Coder-3B-Instruct | DIFF+I | 234 | 50 | 847/873 (97.02%) | 75/100 (75.00%) |
| Qwen3-4B-Instruct-2507 | DIFF | 15 | 72 | 193/230 (83.91%) | 4/23 (17.39%) |
| Qwen3-4B-Instruct-2507 | DIFF+I | 15 | 53 | 194/229 (84.72%) | 4/23 (17.39%) |

JSON valid berarti lolos parser dan skema runner serta tidak terpotong karena batas token. Parser menerima objek JSON pertama dalam respons, termasuk jika dibungkus Markdown; ini bukan persentase respons yang hanya berisi JSON murni. Sensitivitas memakai respons yang sama, tanpa panggilan ulang atau perubahan prompt.
