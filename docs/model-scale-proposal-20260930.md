# Usulan pembanding ukuran dan keluarga model — 30 September 2026

Status: bahan pemilihan model berdasarkan permintaan pengguna, bukan revisi
protokol yang sudah dibekukan. Tidak ada unduhan bobot atau inferensi baru
dalam penelusuran ini. Model card dan paper primer diperiksa 30 September 2026.

Menambahkan model 7–8B dapat menguji apakah keterbatasan hasil berhubungan
dengan kapasitas model. Hasil D82 menunjukkan kegagalan format masih besar,
sehingga ukuran model tidak boleh langsung diasumsikan sebagai penyebab.
Tujuan perbandingan adalah mengukur recall, FPR, validitas JSON, dan biaya,
termasuk ketika model lebih besar tidak menang.

## Kelompok ukuran

Gunakan kelompok operasional berdasarkan jumlah parameter total yang
dilaporkan pengembang, disertai angka parameter tiap checkpoint:

| Kelompok | Batas parameter | Contoh | Peran |
|---|---|---|---|
| A | 1 ≤ P < 5 miliar | Model nominal 1,5B, 3B, 4B | Model kecil |
| B | 5 ≤ P < 10 miliar | Model nominal 6,7B, 7B, 8B, 9B | Pembanding kapasitas lebih tinggi |
| C | 10 ≤ P < 20 miliar | Model nominal 14B | Perluasan opsional |

Ini definisi penelitian ini, bukan standar universal. Batas tersebut tidak
tumpang tindih dan mengakomodasi nama yang dibulatkan: Qwen3-8B sebenarnya
8,2B, Qwen2.5-Coder-7B 7,61B. Laporkan metrik per model; jangan hanya membuat
rerata kelompok lalu menyimpulkan semua model kelompok B lebih baik.
Jumlah parameter juga dapat ditampilkan sebagai sumbu kontinu.

## Kandidat dan alasan pemilihan

| Kandidat | Parameter dari card | Prioritas/peran | Catatan |
|---|---:|---|---|
| [Qwen2.5-Coder-3B-Instruct](https://huggingface.co/Qwen/Qwen2.5-Coder-3B-Instruct) | 3,09B | Pertahankan baseline | Model kode yang sudah dievaluasi |
| [Qwen3-4B-Instruct-2507](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507) | 4,0B | Pertahankan baseline | Checkpoint non-thinking yang sudah dievaluasi |
| [Qwen2.5-Coder-7B-Instruct](https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct) | 7,61B | Tambahan pertama | Perbandingan ukuran dalam seri Coder yang sama dengan 3B; konfigurasi bawaan mendukung 32.768 token |
| [Qwen3-8B](https://huggingface.co/Qwen/Qwen3-8B) | 8,2B | Tambahan kedua | Pembanding Qwen lebih besar; kunci `enable_thinking=False` untuk rancangan non-thinking |
| [Llama-3.1-8B-Instruct](https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct) | Nominal 8B | Tambahan lintas keluarga pada jalur 32K | Model general-purpose dengan konteks 128K; bukan detektor npm yang dilatih khusus |
| [DeepSeek-Coder-6.7B-Instruct](https://huggingface.co/deepseek-ai/deepseek-coder-6.7b-instruct) | 6,7B | Pembanding kode yang dekat dengan literatur npm | Konteks 16K, perlu jalur perbandingan dengan input yang disamakan |
| [Qwen2.5-Coder-14B-Instruct](https://huggingface.co/Qwen/Qwen2.5-Coder-14B-Instruct) | 14,7B | Opsional, setelah pemeriksaan memori | BF16 dan konteks 32K tidak layak diasumsikan muat pada satu GPU 32 GB |

Usulan tahap pertama: **empat model**, yaitu dua baseline yang sudah ada
ditambah Qwen2.5-Coder-7B dan Qwen3-8B. Jalankan DIFF dan DIFF+I pada semuanya.
Jika memakai kembali 973 pair eksploratif dengan prompt/protokol tetap,
dua model baru berarti 3.892 panggilan tambahan dan total 7.784 respons pada
empat model. Angka ini bukan rancangan ukuran test final.

Qwen2.5-Coder 3B versus 7B merupakan perbandingan dalam seri yang lebih
terkendali, tetapi tetap bukan eksperimen yang mengubah satu parameter
arsitektur saja. Qwen3-4B-Instruct-2507 versus Qwen3-8B juga berbeda tahap
post-training/checkpoint; jangan menyebut selisihnya efek murni ukuran.
Jika ingin kurva ukuran Qwen3 yang lebih konsisten, gunakan pasangan rilis
yang sepadan sebagai lengan baru dan pertahankan hasil 2507 secara terpisah.

Tahap lintas keluarga dapat menambahkan Llama-3.1-8B pada jalur konteks 32K.
DeepSeek-Coder-6.7B paling relevan sebagai pembanding kode dari studi npm,
tetapi sebaiknya ditempatkan pada jalur 16K bersama setidaknya
Qwen2.5-Coder-7B. Rekonstruksi masukan yang sama dan sisihkan ruang output
untuk kedua tokenizer. Jangan memotong masukan hanya untuk DeepSeek lalu
mengatribusikan perbedaan hasil kepada model. Jangan menghapus pair panjang
diam-diam atau menggunakan hasil subset sebagai pengganti metrik seluruh data.

## Bukti dari penelitian terkait

- [Nguyen et al., *Leveraging Code Slicing for LLMs-based Malicious NPM Package Detection*, v3](https://arxiv.org/html/2512.12313v3)
  memilih DeepSeek-Coder 6,7B instruction-tuned. Tabel 5 melaporkan recall
  72,90% dan F1 83,32% dengan taint slicing. Hasil terbatas pada 2.537 paket
  yang menghasilkan slice tidak kosong. Ini alasan relevansi model,
  bukan target hasil yang dapat dibandingkan langsung dengan smart-diff kita.
- [Pang et al., *DistillGuard*, v1](https://arxiv.org/html/2609.28996v1)
  memakai Qwen3-8B dengan LoRA, distilasi GPT-5, dan fitur analisis statis.
  Tabel III melaporkan recall 88,9% dan F1 93,8%. Nilai tersebut milik sistem
  yang dilatih khusus; menjalankan Qwen3-8B tanpa fine-tuning tidak mereplikasi
  DistillGuard dan tidak menjanjikan angka yang sama.

Kedua sumber mendukung pemilihan pembanding lokal yang relevan. Rerun lokal
pada dataset/protokol yang sama diperlukan untuk perbandingan langsung.

## Alternatif generasi lebih baru dan MoE

[Qwen3.5-4B](https://huggingface.co/Qwen/Qwen3.5-4B) dan
[Qwen3.5-9B](https://huggingface.co/Qwen/Qwen3.5-9B) merupakan alternatif
untuk pasangan dari generasi yang lebih baru. Model card mencakup model
bahasa dengan vision encoder; evaluasi ini hanya membutuhkan teks. Card
9B menyediakan mode language-model-only dan pengaturan non-thinking.
Keduanya layak dipertimbangkan sebagai lengan baru jika kebaruan generasi
menjadi prioritas, setelah kompatibilitas runtime, tokenizer, cakupan
parameter yang dihitung, dan memori diverifikasi. Tidak ada bukti dari
penelusuran ini bahwa keduanya pasti lebih baik untuk deteksi npm.

Jangan memasukkan [Qwen3-Coder-30B-A3B-Instruct](https://huggingface.co/Qwen/Qwen3-Coder-30B-A3B-Instruct)
ke kelompok model 3B dense: card mencatat **30,5B total dan 3,3B aktif**.
Jika dipakai, pisahkan analisis MoE dan laporkan keduanya. Parameter aktif
bukan ukuran seluruh bobot yang perlu ditampung.

## Kelayakan RTX 5090 32 GB

Berikut estimasi analitis, **bukan pengukuran deployment**. Asumsi bobot dan
KV cache BF16, satu sequence, panjang total maksimum 32.768, tanpa offload.
Bobot diperkirakan `P × 2 byte`; KV dihitung dengan
`2 × layers × kv_heads × head_dim × sequence_length × 2 byte`.
GiB memakai pembagi 2^30; angka parameter dari card dibulatkan.

| Model | Bobot (GiB) | KV maksimum (GiB) | Subtotal (GiB), belum runtime/aktivasi |
|---|---:|---:|---:|
| Qwen2.5-Coder-7B | 14,17 | 1,75 | 15,92 |
| Qwen3-8B | 15,27 | 4,50 | 19,77 |
| Qwen2.5-Coder-14B | 27,38 | 6,00 | 33,38 |

Sumber arsitektur: konfigurasi resmi
[7B](https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct/raw/main/config.json),
[8B](https://huggingface.co/Qwen/Qwen3-8B/raw/main/config.json), dan
[14B](https://huggingface.co/Qwen/Qwen2.5-Coder-14B-Instruct/raw/main/config.json).
7B/8B layak diperiksa lebih dahulu pada GPU saat ini; subtotal bukan jaminan
muat. Alokasi vLLM 0,65 yang dipakai sebelumnya juga bukan jaminan cukup
untuk model baru dan harus diperiksa sebelum inferensi.

14B BF16 pada konteks tersebut sudah melebihi kapasitas GPU bahkan sebelum
overhead. Alternatifnya GPU lebih besar, kuantisasi, atau konteks lebih
pendek; setiap alternatif mengubah faktor eksperimen. Jangan membandingkan
14B 4-bit dengan 3B BF16 lalu menyebut selisihnya efek ukuran saja. Bila
memilih jalur kuantisasi, sertakan pembanding ukuran lebih kecil dengan
metode/presisi kuantisasi yang sepadan.

## Hal yang harus dibekukan sebelum evaluasi tambahan

1. Tentukan apakah model besar hanya baseline tambahan atau masuk seluruh
   ablation RAG. Usulan hemat cakupan: baseline besar pada DIFF/DIFF+I dahulu;
   jangan memperluas klaim RAG ke model yang belum diuji konfigurasi retrieval.
2. Pertahankan identitas pair, isi masukan, aturan parser, perlakuan invalid,
   dan output budget yang sama pada tiap lengan sebanding. Gunakan template
   chat resmi masing-masing model dan audit tokenisasi; jumlah token tidak
   harus identik pada keluarga tokenizer berbeda.
3. Kunci thinking/non-thinking dan kebijakan sampling secara eksplisit.
   Qwen3-8B thinking aktif secara default; card menyarankan sampling berbeda
   dari greedy. Pemilihan greedy bersama untuk kontrol boleh menjadi keputusan
   metode, tetapi jangan disebut setting optimal yang disarankan pengembang.
4. Jika format direvisi pada dev set, ulangi semua model pembanding dengan
   revisi yang sama. Hasil lama dengan prompt berbeda tetap menjadi arsip.
5. Catat revisi checkpoint, rilis/cutoff temporal, dtype/kuantisasi, konteks,
   versi runtime, dan kebutuhan memori. Model lebih baru juga mengubah risiko
   kontaminasi insiden, bukan hanya kemampuan atau jumlah parameter.
6. Laporkan recall, FPR TYP/HN jika label tersedia, validitas JSON, macro recall
   kampanye, sensitivitas invalid, token, latency, dan memori. Jangan memilih
   model hanya berdasarkan accuracy atau recall. Anotasi gold dan G1/G2 tetap
   diperlukan untuk studi utama.

Dokumen penelitian aktif masih menyatakan lingkup 3–4B. Mengubah lingkup
utama menjadi lintas ukuran memerlukan penyesuaian RQ1, kontribusi, metode,
dan rencana statistik di `docs/`, lalu keputusan baru sebelum pembekuan.
Usulan ini belum mengubah dokumen tersebut atau menggantikan D81/D82.
