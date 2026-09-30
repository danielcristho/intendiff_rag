# Evaluasi data asli dengan batas keluaran 2.048 token — 29 September 2026

**Eksploratif terhadap label sumber; bukan evaluasi gold atau hasil konfirmatori.**

Diperbarui: 2026-09-30T01:56:43.706081+00:00.

Run selesai: 3892/3892. Status lengkap: True.

Dataset: 873 MAL berlabel sumber + 100 TYP yang diasumsikan benign. Seluruh pair dipakai pada DIFF dan DIFF+I untuk kedua model, greedy/seed 0.

| Model | Konfigurasi | MAL ditandai malicious | FPR TYP | JSON valid | Median ms | p95 ms |
|---|---|---:|---:|---:|---:|---:|
| Qwen2.5-Coder-3B-Instruct | DIFF | 738/873 (84.54%) | 48/100 (48.00%) | 845/973 | 1088.2 | 14214.5 |
| Qwen2.5-Coder-3B-Instruct | DIFF+I | 629/873 (72.05%) | 49/100 (49.00%) | 730/973 | 1414.1 | 14281.8 |
| Qwen3-4B-Instruct-2507 | DIFF | 480/873 (54.98%) | 6/100 (6.00%) | 698/973 | 828.6 | 15325.9 |
| Qwen3-4B-Instruct-2507 | DIFF+I | 552/873 (63.23%) | 3/100 (3.00%) | 743/973 | 892.6 | 14114.4 |

Output tidak valid dihitung benign sesuai D18. Sensitivitas ketika output tidak valid dihitung malicious, macro recall per kampanye, dan token tersedia di `summary.json`. Error transport tidak dianggap prediksi.

Angka MAL mengukur kesesuaian terhadap label sumber, bukan recall terhadap anotasi manusia. Tidak ada evaluasi HN atau klaim manfaat RAG; card KB belum ditulis dan diverifikasi. Dataset ini belum memakai kuota dan cap kampanye test final. Perbedaan model/config dilaporkan apa adanya tanpa penyetelan prompt.

Latency mencakup request awal, dengan prefix caching aktif; angka ini bukan benchmark RQ4. Respons mentah, evidence, finish reason, token, dan latency setiap panggilan tersedia dalam `results.jsonl`. Model, revisi, parameter, dan checksum masukan tersedia dalam `protocol.json`.

MAL mencakup 224 klaster operasional; klaster terbesar memuat 607/873 pair. Macro recall memberi bobot yang sama pada tiap klaster dan tersedia di bawah. Angka ini tetap memakai label sumber dan definisi klaster §3.6, bukan validasi insiden independen.

| Model | Konfigurasi | Macro recall sumber per klaster |
|---|---|---:|
| Qwen2.5-Coder-3B-Instruct | DIFF | 78.69% |
| Qwen2.5-Coder-3B-Instruct | DIFF+I | 56.48% |
| Qwen3-4B-Instruct-2507 | DIFF | 42.38% |
| Qwen3-4B-Instruct-2507 | DIFF+I | 54.05% |

Diagnostik keluaran dan sensitivitas aturan invalid-as-malicious:

| Model | Konfigurasi | Batas 2.048 token | Invalid lainnya | MAL ditandai (sensitivitas) | FPR TYP (sensitivitas) |
|---|---|---:|---:|---:|---:|
| Qwen2.5-Coder-3B-Instruct | DIFF | 75 | 53 | 842/873 (96.45%) | 72/100 (72.00%) |
| Qwen2.5-Coder-3B-Instruct | DIFF+I | 118 | 125 | 847/873 (97.02%) | 74/100 (74.00%) |
| Qwen3-4B-Instruct-2507 | DIFF | 7 | 268 | 748/873 (85.68%) | 13/100 (13.00%) |
| Qwen3-4B-Instruct-2507 | DIFF+I | 2 | 228 | 773/873 (88.55%) | 12/100 (12.00%) |

JSON valid berarti lolos parser dan skema runner serta tidak terpotong karena batas token. Parser menerima objek JSON pertama dalam respons, termasuk jika dibungkus Markdown; ini bukan persentase respons yang hanya berisi JSON murni. Sensitivitas memakai respons yang sama, tanpa panggilan ulang atau perubahan prompt.

Total keluaran invalid: 876; 202 mencapai batas token, 641 memiliki sintaks JSON tidak valid, 33 gagal memenuhi skema, dan 0 tanpa objek JSON. Jumlah ini menunjukkan bahwa metrik deteksi juga dipengaruhi kepatuhan format, sehingga hasil utama perlu dibaca bersama tabel sensitivitas.
