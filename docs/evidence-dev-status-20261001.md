# Riwayat D85: startup awal terhambat CUDA

**Pembaruan 1 Oktober 2026, 21:42 UTC+7: CUDA pulih setelah restart WSL
yang disetujui pengguna; seluruh 160 inferensi selesai dan terverifikasi.**
Lihat [hasil akhir D85](evidence-dev-results-20261001.md). Catatan di bawah
dipertahankan sebagai riwayat sebelum pemulihan, bukan status aktif.

1 Oktober 2026. [Protokol](evidence-dev-20261001.md) dibekukan sebelum
prediksi. **0/160 generasi terlaksana**, bukan eksperimen yang selesai.
Tidak ada hasil FPR, recall, atau peningkatan akurasi baru.

## Yang selesai

- Indeks bukti `pipeline/evidence.py`: ID stabil, path/nomor baris, pembedaan
  added/deleted/context/metadata, serta pemeriksaan ID tidak ditemukan.
- Delapan pengujian lulus; 1.035 smart-diff review dapat diindeks. Header
  yang menyerupai kode tambahan tidak salah diklasifikasikan sebagai path.
- 32 kandidat HN nyata dipilih deterministik dari 126 yang memenuhi syarat.
  Masukan, prompt, decoder schema, lima arm, dan bobot dipin. 128 prompt
  tahap pertama diaudit; maksimum 24.639 token. Tahap verifier aktual perlu
  kandidat dan akan diperiksa sebelum request. Tidak ada fixture inferensi.
- Input anotasi tanpa prediksi dan daftar paket dev yang harus dikeluarkan
  dari test/KB final tersimpan. Pemisahan kampanye HN masih belum tersedia.
- Audit asal kutipan mencakup 11.676 respons historis: 9.575 JSON valid,
  2.101 invalid. Pada 5.254 respons valid, setidaknya satu kutipan tidak
  cocok sebagai satu baris lengkap setelah mengabaikan spasi tepi atau
  penanda diff. Kategori ini juga mencakup substring/gabungan baris, sehingga
  **bukan** jumlah halusinasi atau kesalahan semantik. Verdict tidak diubah.

## Penghambat lingkungan

Server lokal gagal sebelum inferensi saat `cuInit`. Probe terisolasi
menunjukkan pemanggilan langsung libcuda `cuInit(0)` tanpa PyTorch keluar
dengan SIGSEGV (-11); `torch.cuda.init()` juga -11. NVML/nvidia-smi berhasil
membaca RTX 5090, driver 616.56. Host WSL2 memiliki `/dev/dxg` dan pustaka
`/usr/lib/wsl/lib/libcuda.so.1`; ketiadaan `/dev/nvidia0` sendiri bukan
diagnosis kegagalan karena ini WSL.

Bukti melokalisasi kegagalan pada inisialisasi CUDA di lingkungan saat ini,
belum membuktikan penyebab dasar atau perlunya versi driver tertentu.
Tidak ada perubahan driver, reset GPU, restart WSL, atau penghapusan hasil.
Controller/server percobaan sudah berhenti. Protokol dan log kegagalan
dipertahankan; tidak ada prediksi yang dibuang atau hasil fiktif pengganti.

## Kelanjutan konkret

Pulihkan inisialisasi CUDA host terlebih dahulu. Setelah probe menghasilkan
cuInit=0 dan torch.cuda.init berhasil, jalankan evaluator beku. Jangan
mengubah prompt karena kegagalan startup ini. Metrik pertama tetap format,
keterlacakan kutipan, dan transisi pada dev; gold independen diperlukan
untuk menilai apakah alarm yang berkurang merupakan FP atau deteksi yang
hilang. Uji MB/MM memerlukan card benign/malicious yang diverifikasi.

Artefak:

- [Verifikasi persiapan](../data/evaluation/evidence-dev-20261001/verification.json)
- [Probe CUDA](../scratchpad/fpr-audit-20261001/cuda-probe.json)
- [Audit kutipan historis](../scratchpad/fpr-audit-20261001/evidence-provenance.json)
- [Prosedur anotasi dev](../data/evaluation/evidence-dev-20261001/ANNOTATION.md)

Parser dev memvalidasi schema persis pada semua arm. Parser historis lebih
longgar terhadap extra keys/capitalization; angka validitas dev kelak tidak
dibandingkan langsung sebagai efek tunggal terhadap D82–D84. Pembanding
LEGACY-I/SCHEMA-I di cohort baru memakai validator yang sama. Penambahan ID
dan urutan field pada IDS-I adalah intervensi gabungan, dijelaskan di protokol.
