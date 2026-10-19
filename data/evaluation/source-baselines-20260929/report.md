# Evaluasi baseline data asli — 29 September 2026

**Eksploratif terhadap label sumber; bukan evaluasi gold atau hasil konfirmatori.**

Diperbarui: 2026-09-29T12:18:38.775796+00:00.

Run selesai: 3892/3892. Status lengkap: True.

Dataset: 873 MAL berlabel sumber + 100 TYP yang diasumsikan benign. Seluruh pair dipakai pada DIFF dan DIFF+I untuk kedua model, greedy/seed 0.

| Model | Konfigurasi | MAL ditandai malicious | FPR TYP | JSON valid | Median ms | p95 ms |
|---|---|---:|---:|---:|---:|---:|
| Qwen2.5-Coder-3B-Instruct | DIFF | 704/873 (80.64%) | 45/100 (45.00%) | 803/973 | 1084.3 | 3622.6 |
| Qwen2.5-Coder-3B-Instruct | DIFF+I | 595/873 (68.16%) | 43/100 (43.00%) | 689/973 | 1407.0 | 3656.2 |
| Qwen3-4B-Instruct-2507 | DIFF | 418/873 (47.88%) | 6/100 (6.00%) | 636/973 | 802.8 | 4026.2 |
| Qwen3-4B-Instruct-2507 | DIFF+I | 495/873 (56.70%) | 3/100 (3.00%) | 687/973 | 871.0 | 4082.5 |

Output tidak valid dihitung benign sesuai D18. Sensitivitas ketika output tidak valid dihitung malicious, macro recall per kampanye, dan token tersedia di `summary.json`. Error transport tidak dianggap prediksi.

Angka MAL mengukur kesesuaian terhadap label sumber, bukan recall terhadap anotasi manusia. Tidak ada evaluasi HN atau klaim manfaat RAG; card KB belum ditulis dan diverifikasi. Dataset ini belum memakai kuota dan cap kampanye test final. Perbedaan model/config dilaporkan apa adanya tanpa penyetelan prompt.

Latency mencakup request awal, dengan prefix caching aktif; angka ini bukan benchmark RQ4. Respons mentah, evidence, finish reason, token, dan latency setiap panggilan tersedia dalam `results.jsonl`. Model, revisi, parameter, dan checksum masukan tersedia dalam `protocol.json`.

MAL mencakup 224 klaster operasional; klaster terbesar memuat 607/873 pair. Macro recall memberi bobot yang sama pada tiap klaster dan tersedia di bawah. Angka ini tetap memakai label sumber dan definisi klaster §3.6, bukan validasi insiden independen.

| Model | Konfigurasi | Macro recall sumber per klaster |
|---|---|---:|
| Qwen2.5-Coder-3B-Instruct | DIFF | 76.66% |
| Qwen2.5-Coder-3B-Instruct | DIFF+I | 50.29% |
| Qwen3-4B-Instruct-2507 | DIFF | 37.22% |
| Qwen3-4B-Instruct-2507 | DIFF+I | 49.82% |

Diagnostik keluaran dan sensitivitas aturan invalid-as-malicious:

| Model | Konfigurasi | Batas 512 token | Invalid lainnya | MAL ditandai (sensitivitas) | FPR TYP (sensitivitas) |
|---|---|---:|---:|---:|---:|
| Qwen2.5-Coder-3B-Instruct | DIFF | 143 | 27 | 843/873 (96.56%) | 76/100 (76.00%) |
| Qwen2.5-Coder-3B-Instruct | DIFF+I | 234 | 50 | 847/873 (97.02%) | 75/100 (75.00%) |
| Qwen3-4B-Instruct-2507 | DIFF | 76 | 261 | 747/873 (85.57%) | 14/100 (14.00%) |
| Qwen3-4B-Instruct-2507 | DIFF+I | 67 | 219 | 772/873 (88.43%) | 12/100 (12.00%) |

JSON valid berarti lolos parser dan skema runner serta tidak terpotong karena batas token. Parser menerima objek JSON pertama dalam respons, termasuk jika dibungkus Markdown; ini bukan persentase respons yang hanya berisi JSON murni. Sensitivitas memakai respons yang sama, tanpa panggilan ulang atau perubahan prompt.

Total keluaran invalid: 1077; 520 mencapai batas token, 525 memiliki sintaks JSON tidak valid, 32 gagal memenuhi skema, dan 0 tanpa objek JSON. Jumlah ini menunjukkan bahwa metrik deteksi juga dipengaruhi kepatuhan format, sehingga hasil utama perlu dibaca bersama tabel sensitivitas.
