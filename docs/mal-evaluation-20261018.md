# Evaluasi tambahan MAL, 18 Oktober 2026 (D105)

Pengguna meminta menjalankan seluruh evaluasi yang siap dan meninggalkan batch
berjalan mandiri. D101/D102 sudah lengkap untuk enam model. Qwen3-8B gagal
gate format dev (49/60, 81,67%); tidak mengubah prompt/output budget agar lolos.
Tidak ada fine-tuning. Semua hasil lama dipertahankan dan diverifikasi ulang.

## Cohort dan protokol

- Dataset tambahan D104: 96 pair MAL sumber / 65 klaster kampanye, termasuk
  tiga pair D103. SHA-256 dan seluruh pin preparation diverifikasi sebelum rilis.
- Sifatnya evaluasi tambahan sesudah hasil historis diketahui, bukan test
  konfirmatori yang ditetapkan sebelum penelitian. Tidak memilih konfigurasi
  berdasarkan hasil test baru. Pendahulu tanpa advisory bukan gold benign.
- Enam konfigurasi D101 tetap: DIFF, DIFF+I, DIFF+I+M, DIFF+I+MM,
  DIFF+I+MB, DIFF+MB. KB 75 card, prompt, schema, parser, sampling suhu0/seed0,
  output512 token, model/revisi/opsi chat tetap sesuai snapshot masing-masing.
- Snapshot terpisah per model dalam `data/evaluation/source-rag-mal-20261018/`.
  Enam model eligible: qwen3, qwen25, qwen25_7b, phi4_mini, llama31_8b,
  granite33_8b. Target 576 respons/model, total3.456, di luar warm-up.
- Audit seluruh prompt dengan tokenizer/chat template masing-masing. Aturan
  kapasitas konteks/KV D102 berlaku; tidak memotong ulang input atau membuang
  pair untuk menyesuaikan satu model. Gagal audit berarti gagal persiapan.
- Dev10pair dan respons60/model dipakai ulang karena request identik; verifier
  merekonstruksi hash request dan token serta mengharuskan kelengkapan+JSON>=90%.
  Tidak mengklaim ini sebagai inferensi dev baru. Warm-up tetap tiga request dev
  pada setiap sesi server. Test lama11.406/model tidak dijalankan ulang.
- Model dilayani berurutan di localhost8101, bfloat16, satu request aktif.
  Sampel tetap hanya teks input; tidak menginstal atau menjalankan kode paket.

## Pelaporan yang ditetapkan sebelum inferensi tambahan

TPR tambahan dilaporkan TERPISAH dari33MAL historis. Seluruh cohort tambahan MAL,
sehingga tidak menginterpretasikan accuracy-nya sebagai performa kedua kelas:
FPR dan balanced accuracy cohort tambahan tidak terdefinisi. Laporkan confusion
count, TPR pair, rata-rata TPR per kampanye, CI95% bootstrap kampanye10.000resample
seed2026, validitas JSON, serta biaya token/latensi. Invalid dianggap benign pada
hasil utama dan malicious pada sensitivitas. Perbandingan paired antar-arm memakai
kontras D101 dan bootstrap kampanye, bukan memilih arm terbaik sesudah melihat test.

`summary.json` juga memuat metrik historis dan gabungan129MAL+1.868TYP (1.997pair).
Gabungan hanya deskriptif: FPR menggunakan ulang1.868TYP lama, bukan pengukuran
holdout benign baru. Tidak memperlakukan129pair sebagai129kampanye atau freshholdout.
Tidak memakai CI independen-pair untuk menyatakan kepastian cohort berkelompok.

## Operasional

Persiapan sebelum inference:

```bash
.venv/bin/python -u pipeline/mal_eval_prepare.py --out data/evaluation/source-rag-mal-20261018
```

Mulai/resume batch yang sudah siap (memiliki lock; melewati respons sukses):

```bash
scripts/source-rag/run-mal.sh
scripts/source-rag/status-mal.sh
```

Batch yang dilepas dari terminal memakai `start_new_session=True`, stdin ditutup,
stdout/stderr ke `batch.log`, PID di `batch.pid`. Proses tetap membutuhkan host
menyala. Status dan `completion.json` membedakan lengkap, berjalan, dan gagal;
gagal satu model dicatat lalu model berikutnya dicoba. Error teknis tidak dihitung
sebagai prediksi. `results.md`/`summary.json` ditulis sesudah verifikasi per model.
Jangan mengubah helper/protokol/input yang dipin selama batch berlangsung.
