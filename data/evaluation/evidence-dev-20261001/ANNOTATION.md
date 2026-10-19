# Anotasi dev D85

Gunakan hanya `annotation-input.jsonl` untuk pelabelan independen. File
`results.jsonl` dan `summary.json` berisi prediksi dan tidak boleh dijadikan
dasar label. Tidak ada gold yang telah dibuat untuk cohort ini.

Dua anotator meninjau masing-masing 32 pair secara independen. Ikuti
`docs/annotation-20260928.md`: label malicious/benign/skip, bukti kode,
sumber tujuan sah, alasan, dan kategori HN bila benign terverifikasi.
Jangan menjalankan paket, script instalasi, atau endpoint dalam sampel.
Simpan identitas serta keputusan masing-masing sebelum rekonsiliasi.

Predikat HN pada input berarti kandidat yang dipilih berdasarkan sinyal,
bukan keputusan benign. Jika konteks tidak cukup, gunakan skip dengan
alasan; jangan memaksakan label. Jangan menganggap semua alarm sebagai FP.

Semua paket pada `dev-exclusions.jsonl` telah digunakan untuk pengembangan:
keluarkan paket dan klon terkait dari evaluasi final serta KB retrieval.
Pemeriksaan kemiripan kampanye HN belum selesai. Label dev kelak hanya
mendukung analisis pengembangan, bukan mengubahnya menjadi holdout.
