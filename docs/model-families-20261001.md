# Eksplorasi lintas keluarga model — 1 Oktober 2026 (D84)

**Status: bobot terverifikasi, protokol dibekukan, controller evaluasi berjalan.** Pengguna meminta
eksplorasi model lain setelah D83 selesai. Dua model dipilih berdasarkan
akses, dukungan runtime, konteks, dan memori sebelum melihat prediksi.

## Model terpilih

| Model | Parameter aktual dari metadata snapshot | Kelompok | Pembanding historis |
|---|---:|---|---|
| [Microsoft Phi-4-mini-instruct](https://huggingface.co/microsoft/Phi-4-mini-instruct) | 3,836B (nominal 3,8B) | A: 1 ≤ P < 5B | Qwen2.5-Coder-3B dan Qwen3-4B-Instruct-2507 |
| [Meta Llama-3.1-8B-Instruct](https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct) | 8,030B (nominal 8B) | B: 5 ≤ P < 10B | Qwen2.5-Coder-7B dan Qwen3-8B |

Phi menambah keluarga model kecil, Llama menambah keluarga sekitar 8B.
Keduanya adalah pembanding instruction-tuned umum; tidak diklaim sebagai
detektor npm yang dilatih khusus. Ini bukan replikasi skor paper pada
dataset atau metode lain, dan tidak mengisolasi efek jumlah parameter.
Greedy digunakan sebagai kontrol bersama, bukan klaim setting optimal
masing-masing pengembang.

## Audit kandidat tanpa inferensi

Lima model ditokenisasi pada seluruh 973 pair × dua konfigurasi. Seluruh
pesan dibuat dari snapshot prompt/input D83 yang tidak diubah. Kolom
"melampaui" mencakup cadangan output 2.048 token; hitungan adalah prompt,
bukan jumlah pair unik. Tidak ada prediksi LLM pada tahap pemilihan ini.

| Kandidat | Konteks native | Prompt maksimum | Prompt melampaui native | Keputusan |
|---|---:|---:|---:|---|
| Phi-4-mini-instruct | 131.072 | 29.919 | 0 | Dipilih; server 32.768 |
| Llama-3.1-8B-Instruct | 131.072 | 29.186 | 0 | Dipilih; akses yang tersedia berhasil, server 32.768 |
| Mistral-7B-Instruct-v0.3 | 32.768 | 39.236 | 109 | Tidak muat untuk seluruh input; perlu jalur dengan input disamakan |
| Granite-3.3-8B-Instruct | 131.072 | 36.617 | 0 | Memerlukan server 49.152; cadangan karena prioritas Llama sudah lolos |
| DeepSeek-Coder-6.7B-Instruct | 16.384 | 37.312 | 167 | Perlu jalur konteks pendek yang disamakan untuk semua pembanding |

Urutan prioritas dan kriteria dicatat di [D84](decisions.md) sebelum
inferensi. Card primer untuk kandidat lain:
[Mistral](https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.3),
[Granite](https://huggingface.co/ibm-granite/granite-3.3-8b-instruct), dan
[DeepSeek](https://huggingface.co/deepseek-ai/deepseek-coder-6.7b-instruct).
Angka token merupakan pengukuran lokal, bukan angka benchmark dari card.
[Audit kandidat](../data/evaluation/model-families-20261001/candidate-audit.json)
dan [pin metadata](../data/evaluation/model-families-20261001/candidate-pins.json)
menyimpan rinciannya. Tidak ada penerimaan syarat akses Llama baru.

Estimasi bobot BF16 + KV pada satu sequence 32K: Phi 7,15 + 4,00 GiB;
Llama 14,96 + 4,00 GiB, belum runtime/aktivasi. Ini estimasi analitis,
bukan puncak memori deployment. Runtime lokal telah memiliki implementasi
`Phi3ForCausalLM` dan `LlamaForCausalLM`; tidak memakai remote Python code.

## Protokol yang dipertahankan

Seluruh 973 pair (873 MAL label sumber + 100 TYP diasumsikan benign), DIFF
dan DIFF+I, BF16, seed 0, temperature 0, top_p 1, output maksimum 2.048,
konteks server 32.768, prefix caching, dan max_num_seqs 1. Alokasi awal
otomatis 0,80 diganti dengan KV cache eksplisit 6 GiB untuk kedua model
setelah kegagalan startup Phi, sebelum ada prediksi.
Prompt/parser/aturan invalid tidak berubah. Tidak ada kuantisasi, tambahan
pemotongan input, pemilihan pair berdasarkan hasil, atau warm-up LLM sintetis.

Template native masing-masing model dipakai dan akan dicocokkan dengan
endpoint server `/tokenize` sebelum request generasi. `generation-config=vllm`
tetap digunakan agar default sampling model tidak mengubah kontrol bersama.
Token akhir giliran dari `generation_config.json` resmi disertakan sebagai
`stop_token_ids`: Phi `[200020,199999]`; Llama `[128001,128008,128009]`.
Keduanya memiliki token akhir jawaban tambahan yang tidak seluruhnya
tercantum dalam `config.json`. Ini bukan stop string buatan, repair JSON,
atau perubahan format prompt. Daftar tersebut dicatat dalam metadata
respons. Kontrol Qwen historis tidak memiliki override request ini.

Target: 3.892 inferensi baru + 7.784 kontrol historis D82/D83 = 11.676
respons, enam model × dua konfigurasi. Artefak baru disimpan di
[`data/evaluation/model-families-20261001/`](../data/evaluation/model-families-20261001/).
Checksum kode, input, tokenizer/bobot, dan kontrol dibekukan sebelum inferensi.
Snapshot lama tidak diubah. Status saat ini:
[controller](../data/evaluation/model-families-20261001/status.json),
[protokol beku](../data/evaluation/model-families-20261001/protocol.json), dan
[pemeriksaan awal](../data/evaluation/model-families-20261001/preflight.json).

## Metrik dan batas interpretasi

Seluruh dua belas kelompok akan dilaporkan: recall MAL sumber, FPR TYP,
validitas/jenis invalid, sensitivitas invalid-as-malicious, macro recall
kampanye, token, dan latency. Perubahan terhadap kedua kontrol Qwen pada
kelompok ukuran yang sama diurai menjadi transisi verdict valid dan
transisi yang melibatkan invalid. Tidak hanya menampilkan model yang menang.

Startup Phi pertama gagal mengalokasikan buffer KV otomatis 15,80 GiB;
bobot sudah termuat, tetapi belum ada request generasi. Penyebab allocator
atau driver belum dipastikan. Cache eksplisit 6 GiB cukup untuk kebutuhan
KV BF16 satu sequence 32K yang terhitung 4 GiB pada kedua model. Pengaturan
ini menggantikan perhitungan cache dari flag alokasi 0,80, sesuai
[konfigurasi vLLM](https://github.com/vllm-project/vllm/blob/main/vllm/config/cache.py).
Protokol awal, semua sumber, dan log kegagalan dipertahankan;
[amendemen sebelum inferensi](../data/evaluation/model-families-20261001/cache-amendment.json)
mencatat perubahan dan checksum asal. Tidak ada perubahan berdasarkan
prediksi atau penghapusan run evaluasi.

Konteks pesan sama, tetapi jumlah token dan template berbeda antar keluarga.
Qwen3B/4B historis memakai alokasi cache otomatis dari GPU 0,65, dan
Qwen7B/8B 0,80; kedua model baru cache eksplisit 6 GiB. Latency antar-sesi
hanya observasional. Pelatihan, tokenizer,
template, dan token akhir native berbeda sehingga selisih bukan efek kausal
ukuran atau arsitektur. Dataset memiliki konsentrasi kampanye dan labelnya
belum gold manusia; cutoff temporal formal model baru juga belum diaudit.
G1/G2, anotasi HN, card KB, dan evaluasi retrieval tetap belum selesai.

Hasil eksploratif boleh ditulis termasuk jika negatif. Revisi format atau
fine-tuning bukan bagian eksperimen ini dan tidak dilakukan diam-diam setelah
melihat prediksi. Pemilihan atau penyetelan lanjutan perlu dev set terpisah.
