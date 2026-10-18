# Evaluasi lima model tambahan — D102

Pengguna menyetujui perluasan setelah melihat hasil dua model utama D101.
Model ditetapkan sebelum inferensi tambahan: Qwen2.5-Coder-7B, Qwen3-8B,
Phi-4-mini, Llama-3.1-8B, dan Granite-3.3-8B. Ini evaluasi tambahan, bukan
klaim bahwa ketujuh model ditentukan sebelum hasil utama diketahui.

## Input dan kontrol

1.901 pair test (33 MAL label sumber + 1.868 TYP assumed-benign), 10 dev,
75 card, enam konfigurasi, teks prompt dan schema disalin dari D101 tanpa
perubahan isi. Target 57.030 respons test dan 300 dev tambahan. Tidak
memasukkan hasil D92 sebagai hasil RAG; dataset dan konfigurasi D92 berbeda.

Model/tokenizer memakai revisi dan hash D92. Qwen3-8B tanpa thinking dan
Granite dengan thinking=false; opsi chat dan stop token dikirim eksplisit,
masuk hash request, dan digunakan dalam audit tokenizer. Semua model tetap
bfloat16, temperature=0, seed=0, output maksimum 512 token, request berurutan.

Teks card mempertahankan batas konstruksi tokenizer Qwen D101. Jumlah token
pada tokenizer baru dicatat di budget.json, termasuk card yang melebihi
512 token atau intent 64 token pada tokenizer tersebut. Tidak ada pemangkasan
ulang yang akan membuat input berbeda antar-model. Konteks minimal 32.768;
jika perlu, dinaikkan ke kelipatan 1.024 yang memuat prompt terbesar+512,
selama di bawah batas native. KV cache minimal 6 GiB dan dihitung dari dimensi
model agar satu sequence muat. Perbedaan sumber daya dilaporkan.

Audit seluruh input selesai tanpa error pada 16 Oktober:

| Model | Prompt dev maksimum | Prompt test maksimum | Konteks layanan | KV cache |
|---|---:|---:|---:|---:|
| Qwen2.5-Coder-7B | 29.800 | 30.144 | 32.768 | 6 GiB |
| Qwen3-8B | 29.804 | 30.148 | 32.768 | 6 GiB |
| Phi-4-mini | 29.323 | 30.306 | 32.768 | 6 GiB |
| Llama-3.1-8B | 28.758 | 30.275 | 32.768 | 6 GiB |
| Granite-3.3-8B | 34.964 | 37.610 | 38.912 | 6 GiB |

Seluruh prompt masih memuat cadangan output 512 token. Pada tokenizer Granite,
satu card (`source-card-aac8cb58c5d375f5`) memiliki intent 67 token, sementara
card lengkapnya 248 token. Teks tetap sama; tidak dipangkas menjadi 64 lagi.
Tidak ada card lengkap melebihi 512 token pada kelima tokenizer. Semua pin
bobot/input lolos saat persiapan. Sebanyak 30 tes terfokus lulus.

## Pelaksanaan dan hasil

Direktori `data/evaluation/source-rag-extra-20261016/` memuat subdirektori
per model, masing-masing dengan kode, protokol, budget, respons dan verifier.
Input induk dan semua bobot diperiksa hash sebelum persiapan/inferensi.
Seluruh dev dijalankan dahulu; tiap model hanya boleh masuk test setelah
audit konteks dan validitas JSON dev >=90%. Kegagalan teknis tidak mengubah
prompt atau membuang pair. Model lain yang lolos tetap dilanjutkan.

`scripts/source-rag/status.sh` menampilkan dua model utama dan lima tambahan.
`scripts/source-rag/run-extra.sh` menjalankan/resume batch tambahan; jangan
menjalankan proses kedua ketika batch masih aktif. File `batch-status.json`
mencatat status termasuk kegagalan, dan `evaluation.log` per model memuat
alasan teknis. `comparison.md` menggabungkan ringkasan yang sudah lengkap
dan terverifikasi; model belum selesai tidak diberi estimasi metrik.

Antrean background diluncurkan dengan PID tersimpan di `batch.pid`, log
`batch.log`. Ia menunggu audit persiapan selesai dan lock dev Qwen7B pertama
dilepas, lalu menjalankan seluruh urutan dev/test. Tidak perlu meluncurkan
`run-extra.sh` lagi selama proses ini masih aktif.

Dev Qwen2.5-Coder-7B selesai dan terverifikasi 60/60 respons, JSON valid
100%, tanpa error request. Coordinator sudah beralih ke batch utama tambahan;
respons dev yang selesai dipakai kembali sesuai snapshot, bukan dihasilkan
ulang. Model lain masih harus melewati dev masing-masing sebelum test.

Pemeriksaan status berikutnya: Phi-4-mini juga lolos 60/60 JSON valid (100%).
Qwen3-8B menyelesaikan 60 respons, tetapi hanya 49 valid (81,67%): sembilan
mencapai batas 512 token dan dua mengandung karakter tab mentah dalam string
JSON. Tidak ada error transport. Release gate >=90% menolak test Qwen3-8B;
ini kegagalan format dev yang dicatat, bukan batch keseluruhan berhenti.
Antrean melanjutkan Llama lalu Granite sebelum test model yang lolos. Status
`verified` berarti hasil diperiksa, bukan bahwa model lolos gate.

Percobaan persiapan awal berhenti sebelum inferensi karena pembaca mengira
pin bobot ada langsung dalam protocol.json D92. D92 menyimpannya di manifest
per model. Pembaca diperbaiki dan ditambah regresi untuk kelima manifest;
artefak awal disimpan di direktori `source-rag-extra-20261016-attempt-model-pins`.

Stage 2 stabilitas/sensitivitas belum otomatis tercakup dalam perluasan model
Stage 1 ini. Kesimpulan deteksi tetap dibatasi label sumber, hanya 33 MAL,
asumsi benign TYP, paparan pretraining yang tidak dapat dikesampingkan, dan
kegagalan/invalid yang harus dilaporkan.
