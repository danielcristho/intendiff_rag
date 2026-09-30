# Evaluasi tambahan model 7B dan 8B — 30 September 2026

**Eksploratif terhadap label sumber; bukan evaluasi gold atau hasil konfirmatori.**

Diperbarui: 2026-09-30T17:04:26.926282+00:00.

Run selesai: 3892/3892. Status lengkap: True.

Dataset: 873 MAL berlabel sumber + 100 TYP yang diasumsikan benign. Seluruh pair dipakai pada DIFF dan DIFF+I untuk kedua model, greedy/seed 0.

| Model | Konfigurasi | MAL ditandai malicious | FPR TYP | JSON valid | Median ms | p95 ms |
|---|---|---:|---:|---:|---:|---:|
| Qwen2.5-Coder-7B-Instruct | DIFF | 811/873 (92.90%) | 65/100 (65.00%) | 915/973 | 1440.5 | 4284.0 |
| Qwen2.5-Coder-7B-Instruct | DIFF+I | 586/873 (67.12%) | 67/100 (67.00%) | 689/973 | 1472.6 | 4872.5 |
| Qwen3-8B | DIFF | 443/873 (50.74%) | 6/100 (6.00%) | 924/973 | 1189.2 | 24288.2 |
| Qwen3-8B | DIFF+I | 422/873 (48.34%) | 3/100 (3.00%) | 929/973 | 1520.1 | 24084.5 |

Output tidak valid dihitung benign sesuai D18. Sensitivitas ketika output tidak valid dihitung malicious, macro recall per kampanye, dan token tersedia di `summary.json`. Error transport tidak dianggap prediksi.

Angka MAL mengukur kesesuaian terhadap label sumber, bukan recall terhadap anotasi manusia. Tidak ada evaluasi HN atau klaim manfaat RAG; card KB belum ditulis dan diverifikasi. Dataset ini belum memakai kuota dan cap kampanye test final. Perbedaan model/config dilaporkan apa adanya tanpa penyetelan prompt.

Latency mencakup request awal, dengan prefix caching aktif; angka ini bukan benchmark RQ4. Respons mentah, evidence, finish reason, token, dan latency setiap panggilan tersedia dalam `results.jsonl`. Model, revisi, parameter, dan checksum masukan tersedia dalam `protocol.json`.

MAL mencakup 224 klaster operasional; klaster terbesar memuat 607/873 pair. Macro recall memberi bobot yang sama pada tiap klaster dan tersedia di bawah. Angka ini tetap memakai label sumber dan definisi klaster §3.6, bukan validasi insiden independen.

| Model | Konfigurasi | Macro recall sumber per klaster |
|---|---|---:|
| Qwen2.5-Coder-7B-Instruct | DIFF | 93.05% |
| Qwen2.5-Coder-7B-Instruct | DIFF+I | 71.47% |
| Qwen3-8B | DIFF | 37.87% |
| Qwen3-8B | DIFF+I | 33.27% |

Diagnostik keluaran dan sensitivitas aturan invalid-as-malicious:

| Model | Konfigurasi | Batas 2.048 token | Invalid lainnya | MAL ditandai (sensitivitas) | FPR TYP (sensitivitas) |
|---|---|---:|---:|---:|---:|
| Qwen2.5-Coder-7B-Instruct | DIFF | 3 | 55 | 869/873 (99.54%) | 65/100 (65.00%) |
| Qwen2.5-Coder-7B-Instruct | DIFF+I | 21 | 263 | 865/873 (99.08%) | 72/100 (72.00%) |
| Qwen3-8B | DIFF | 9 | 40 | 487/873 (55.78%) | 11/100 (11.00%) |
| Qwen3-8B | DIFF+I | 12 | 32 | 460/873 (52.69%) | 9/100 (9.00%) |

JSON valid berarti lolos parser dan skema runner serta tidak terpotong karena batas token. Parser menerima objek JSON pertama dalam respons, termasuk jika dibungkus Markdown; ini bukan persentase respons yang hanya berisi JSON murni. Sensitivitas memakai respons yang sama, tanpa panggilan ulang atau perubahan prompt.

Total keluaran invalid: 435; 45 mencapai batas token, 389 memiliki sintaks JSON tidak valid, 1 gagal memenuhi skema, dan 0 tanpa objek JSON. Jumlah ini menunjukkan bahwa metrik deteksi juga dipengaruhi kepatuhan format, sehingga hasil utama perlu dibaca bersama tabel sensitivitas.
