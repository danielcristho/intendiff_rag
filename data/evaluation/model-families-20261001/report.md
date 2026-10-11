# Evaluasi lintas keluarga: Phi dan Llama — 1 Oktober 2026

**Eksploratif terhadap label sumber; bukan evaluasi gold atau hasil konfirmatori.**

Diperbarui: 2026-10-01T02:24:57.483179+00:00.

Run selesai: 3892/3892. Status lengkap: True.

Dataset: 873 MAL berlabel sumber + 100 TYP yang diasumsikan benign. Seluruh pair dipakai pada DIFF dan DIFF+I untuk kedua model, greedy/seed 0.

| Model | Konfigurasi | MAL ditandai malicious | FPR TYP | JSON valid | Median ms | p95 ms |
|---|---|---:|---:|---:|---:|---:|
| Phi-4-mini-instruct | DIFF | 401/873 (45.93%) | 13/100 (13.00%) | 566/973 | 1058.7 | 20167.7 |
| Phi-4-mini-instruct | DIFF+I | 439/873 (50.29%) | 13/100 (13.00%) | 807/973 | 945.6 | 21062.9 |
| Llama-3.1-8B-Instruct | DIFF | 746/873 (85.45%) | 57/100 (57.00%) | 857/973 | 1342.4 | 12024.7 |
| Llama-3.1-8B-Instruct | DIFF+I | 779/873 (89.23%) | 69/100 (69.00%) | 872/973 | 1381.9 | 13325.0 |

Output tidak valid dihitung benign sesuai D18. Sensitivitas ketika output tidak valid dihitung malicious, macro recall per kampanye, dan token tersedia di `summary.json`. Error transport tidak dianggap prediksi.

Angka MAL mengukur kesesuaian terhadap label sumber, bukan recall terhadap anotasi manusia. Tidak ada evaluasi HN atau klaim manfaat RAG; card KB belum ditulis dan diverifikasi. Dataset ini belum memakai kuota dan cap kampanye test final. Perbedaan model/config dilaporkan apa adanya tanpa penyetelan prompt.

Latency mencakup request awal, dengan prefix caching aktif; angka ini bukan benchmark RQ4. Respons mentah, evidence, finish reason, token, dan latency setiap panggilan tersedia dalam `results.jsonl`. Model, revisi, parameter, dan checksum masukan tersedia dalam `protocol.json`.

MAL mencakup 224 klaster operasional; klaster terbesar memuat 607/873 pair. Macro recall memberi bobot yang sama pada tiap klaster dan tersedia di bawah. Angka ini tetap memakai label sumber dan definisi klaster §3.6, bukan validasi insiden independen.

| Model | Konfigurasi | Macro recall sumber per klaster |
|---|---|---:|
| Phi-4-mini-instruct | DIFF | 35.87% |
| Phi-4-mini-instruct | DIFF+I | 38.12% |
| Llama-3.1-8B-Instruct | DIFF | 76.44% |
| Llama-3.1-8B-Instruct | DIFF+I | 86.67% |

Diagnostik keluaran dan sensitivitas aturan invalid-as-malicious:

| Model | Konfigurasi | Batas 2.048 token | Invalid lainnya | MAL ditandai (sensitivitas) | FPR TYP (sensitivitas) |
|---|---|---:|---:|---:|---:|
| Phi-4-mini-instruct | DIFF | 124 | 283 | 789/873 (90.38%) | 32/100 (32.00%) |
| Phi-4-mini-instruct | DIFF+I | 71 | 95 | 593/873 (67.93%) | 25/100 (25.00%) |
| Llama-3.1-8B-Instruct | DIFF | 2 | 114 | 847/873 (97.02%) | 72/100 (72.00%) |
| Llama-3.1-8B-Instruct | DIFF+I | 22 | 79 | 867/873 (99.31%) | 82/100 (82.00%) |

JSON valid berarti lolos parser dan skema runner serta tidak terpotong karena batas token. Parser menerima objek JSON pertama dalam respons, termasuk jika dibungkus Markdown; ini bukan persentase respons yang hanya berisi JSON murni. Sensitivitas memakai respons yang sama, tanpa panggilan ulang atau perubahan prompt.

Total keluaran invalid: 790; 219 mencapai batas token, 568 memiliki sintaks JSON tidak valid, 3 gagal memenuhi skema, dan 0 tanpa objek JSON. Jumlah ini menunjukkan bahwa metrik deteksi juga dipengaruhi kepatuhan format, sehingga hasil utama perlu dibaca bersama tabel sensitivitas.
