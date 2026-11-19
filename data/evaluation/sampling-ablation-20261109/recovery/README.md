# Penyimpangan eksekusi D111

Dicatat di sini, bukan di `docs/sampling-ablation-20261109.md`, karena dokumen
protokol itu termasuk input yang di-pin di `protocol.json`.

**Re-encode file hasil (11 November 2026).** Pada sel Qwen2.5-Coder T=1,0
seed 0, lima jawaban model memuat U+2028 atau U+0085. Runner menulis hasil dengan
`ensure_ascii=False`, sedangkan `load_jsonl` memecah baris dengan
`str.splitlines`. Akibatnya verifikasi gagal membaca file, walaupun ke-11.982
respons lengkap. Kode runner dibekukan dan di-pin, jadi tidak diubah. File hasil
ditulis ulang dengan escape ASCII oleh `reencode.py`, dan isinya identik per baris
setelah `json.loads`. File asli disimpan di
`test.qwen25.t1.0.s0.results.original-utf8.jsonl`. Sel sisanya dijalankan lewat
`resume.sh`, yang melakukan hal yang sama bila sel lain terkena, dan menyimpan
file aslinya di folder ini.

**Restart server.** Server vLLM Qwen2.5-Coder dinyalakan ulang sebelum sel
T=1,0 seed 1. Seed dikirim per request, jadi sampel tidak bergantung pada sesi
server. Warm-up sesi baru tercatat di `test.qwen25.warmup.jsonl`.

**Batas GPU di WSL2.** Server gagal start enam kali dengan OOM saat mengalokasikan
KV cache 6 GiB, padahal GPU masih kosong ±24 GiB. Pengukuran pada 11 November
menunjukkan bahwa di WSL2 satu proses hanya bisa mengalokasikan GPU sebesar
kira-kira RAM bebas Windows dikurangi ±4,5 GiB:

| RAM bebas Windows | Batas GPU per proses |
|---|---|
| 16,4 GB | 12 GiB |
| 12 GB | 7 GiB |
| 18,7 GB (setelah cache WSL dilepas) | 27 GiB |

Page cache di dalam VM WSL, misalnya dari bobot model 5,8 GB yang terbaca saat
server start, ikut memakan RAM Windows. Restart WSL hanya membantu sementara.
Menaikkan `memory` di `.wslconfig` dari 24 GB ke 28 GB (backup:
`C:\Users\ds-research\.wslconfig.bak-20261111`) tidak menyelesaikan masalah.
`resume.sh` sekarang menjalankan `evict_cache.py`, yang melepas page cache bobot
dan file release setiap 2 detik dengan `posix_fadvise(DONTNEED)`. Cara ini tidak
menyentuh request, flag server, maupun hasil.
