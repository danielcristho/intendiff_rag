# Referensi model open-weight untuk deteksi paket — 29 September 2026

Sumber primer diperiksa pada 29 September 2026. Angka berikut adalah yang
dilaporkan penulis, bukan hasil reproduksi lokal. Model open-weight dalam
paper tidak otomatis berarti seluruh eksperimen dilakukan pada mesin lokal.

| Referensi | Model dan peran | Hasil yang dilaporkan | Batas perbandingan |
|---|---|---|---|
| Ryan et al., *An Evaluation of Large Language Models for Detection of Malicious Python Packages*, arXiv v3 | Qwen3-4B sebagai detektor; juga Qwen3 Coder 30B | Tabel III: Qwen3-4B zero-shot, temperature 0, F1 0,82; rerata 15 konfigurasi 0,69 | PyPI, bukan npm. Task-1 memakai 103 paket (10 malicious, 93 benign), satu file per paket, dari korpus 4.070. Nama keluarga model tidak membuktikan checkpoint identik dengan Qwen3-4B-Instruct-2507 kita. |
| Pang et al., *DistillGuard*, arXiv v1, 24 September 2026 | Qwen3-8B dengan LoRA, distilasi dari GPT-5, dan analisis statis; mendukung inferensi offline | Tabel III: accuracy 95,3%, precision 99,4%, recall 88,9%, F1 93,8% | Paket npm utuh; ada pelatihan khusus. Bukan hasil Qwen3 dasar tanpa fine-tuning. |
| *PDCG-RuleDetector*, Journal of King Saud University Computer and Information Sciences, 2026 | Qwen2.5-Coder-32B-Instruct membangkitkan aturan; aturan ditinjau manusia, fitur dinilai Random Forest | §5.2: recall 89,3% untuk sistem dengan aturan hasil Qwen | Bukan Qwen 3B sebagai classifier langsung. Jangan mengatribusikan hasil utama sistem yang memakai aturan GPT-4o kepada Qwen. |
| Nguyen et al., *Leveraging Code Slicing for LLMs-based Malicious NPM Package Detection*, arXiv v3 | DeepSeek-Coder-6.7B dengan taint-based slicing | Tabel 5: accuracy 87,04%, recall 72,90%, F1 83,32% | Hanya 2.537 paket yang menghasilkan slice tidak kosong. Penulis mengakui bias seleksi; bukan evaluasi seluruh korpus atau diff update. |

Sumber:

- [Ryan, metode §IV-E dan Tabel III](https://arxiv.org/html/2602.16304v3).
- [DistillGuard, metode dan Tabel III](https://arxiv.org/html/2609.28996v1).
- [PDCG-RuleDetector, §5.2](https://link.springer.com/article/10.1007/s44443-026-01121-7).
- [Nguyen, Tabel 5 dan batas validitas](https://arxiv.org/html/2512.12313v3).

## Pemakaian dalam penelitian ini

Wyss tetap referensi utama untuk unit analisis pembaruan. Ryan memberi
pembanding ukuran dan keluarga model; Nguyen memberi pembanding npm dengan
model kode open-weight; DistillGuard memberi konteks Qwen yang dilatih khusus;
PDCG menunjukkan penggunaan Qwen untuk membangun aturan, bukan verdict langsung.

Angka F1 atau accuracy mereka tidak boleh dibandingkan langsung dengan recall
kita. Bahkan metrik bernama sama memerlukan perhatian terhadap unit analisis,
rasio kelas, seleksi sampel, penanganan kegagalan, dan konfigurasi inferensi.

Klaim kebaruan harus berfokus pada kombinasi yang benar-benar diteliti:
smart-diff pembaruan npm, model 3–4B tanpa fine-tuning, intent versi sebelumnya,
retrieval contrastive, dan hard negatives. Klaim luas bahwa deteksi paket
berbahaya belum pernah memakai model lokal/Qwen tidak sesuai sumber ini.
Daftar ini bukan tinjauan sistematis yang membuktikan ketiadaan studi identik.
