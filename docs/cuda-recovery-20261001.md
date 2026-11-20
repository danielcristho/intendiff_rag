# Percobaan ulang CUDA untuk D85

**Pembaruan:** setelah restart WSL yang disetujui pengguna, probe
`resume-probe-20261001T143835Z.json` berhasil dan 160 inferensi D85 selesai.
[Hasil dan verifikasi](evidence-dev-results-20261001.md). Bagian berikut
merekam diagnosis serta prosedur sebelum pemulihan, bukan blocker aktif.

Permintaan pengguna: mencoba melanjutkan lagi setelah startup gagal.
Pemeriksaan ulang tetap menunjukkan `cuInit` dan PyTorch SIGSEGV (-11).
Inferensi D85 masih 0/160; prompt/input/protokol tidak diubah.

## Diagnosis tambahan

- Memuat `/usr/lib/wsl/lib/libcuda.so.1` secara eksplisit: gagal -11.
- Python sistem, tanpa variabel LD_*, CUDA_*, NVIDIA_* dan PYTHON*: gagal -11.
- Trace loader menunjukkan bridge WSL memuat driver NVIDIA dari
  `nv_dispi.inf_amd64_a3944b54ff18b284`, lalu pesan lookup simbol DXCore
  seperti `D3DKMTOpenSyncObjectFromNtHandle` dan `D3DKMTCreateNativeFence`.
- WSL 2.7.14.0, kernel 6.18.33.2-2, DXCore 10.0.26100.1-240331-1435,
  Windows 10.0.26200.9457. NVIDIA 616.56 tetap terbaca melalui NVML.

Ini mengurangi kemungkinan masalah khusus venv atau pemilihan libcuda dari
path yang salah. Pesan simbol tidak membuktikan penyebab crash: pencarian
simbol opsional juga bisa menghasilkan pesan tersebut. Pola mirip dilaporkan
di [issue Microsoft WSL](https://github.com/microsoft/WSL/issues/14446),
tetapi laporan pihak lain bukan konfirmasi penyebab pada host ini.

## Langkah pemulihan yang dapat dicoba

Restart WSL dari Windows setelah seluruh pekerjaan WSL aman dihentikan.
Ini percobaan pemulihan, bukan jaminan perbaikan. Perintah PowerShell:

```powershell
wsl --shutdown
```

[Dokumentasi Microsoft](https://learn.microsoft.com/en-us/windows/wsl/basic-commands#shutdown)
menyatakan perintah ini menghentikan seluruh distro aktif dan VM WSL2.
Karena juga memutus sesi serta layanan lain, belum dijalankan otomatis;
perlu persetujuan eksplisit sebelum menghentikan lingkungan bersama.
Tidak menginstal driver Linux ke WSL, sesuai
[panduan NVIDIA](https://docs.nvidia.com/cuda/wsl-user-guide/index.html).

Setelah membuka kembali WSL, dari root repositori:

```bash
.venv/bin/python scratchpad/cuda-recovery-20261001/resume.py
```

Launcher memeriksa cuInit, PyTorch, dan satu operasi tensor lokal. Jika gagal,
ia keluar tanpa inferensi. Jika berhasil, ia menjalankan evaluator D85 beku
yang memeriksa checksum dan lock. Tidak ada revisi prompt atau penghapusan
hasil. Pemeriksaan tensor adalah diagnosis perangkat, bukan smoke test
LLM atau data evaluasi sintetis. Jika setelah restart masih gagal, diperlukan
pemeriksaan host Windows/WSL/driver lebih lanjut sebelum batch dapat jalan.

Log tersimpan di `scratchpad/cuda-recovery-20261001/diagnosis.json` dan
`loader_trace.stderr.log`. Script diagnosis tidak mengubah sistem.
