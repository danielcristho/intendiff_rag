# Uji signifikansi revisi naskah, 26 Oktober 2026

Nilai p dihitung dari **71.892 respons tersimpan**: enam model, enam konfigurasi,
dan 1.997 pasangan pembaruan. Tidak ada inferensi model baru. Jumlah positif
seluruh konfigurasi dan besar perbedaan diverifikasi terhadap `metrics.csv` dan
`contrasts.csv` pada `data/writing/paper-20261018/`. Identitas pasangan, label,
hash diff, kelengkapan respons, dan pengelompokan kampanye juga diperiksa.

## Metode

- Uji berpasangan dua sisi dengan pembalikan tanda pada **tingkat kampanye**.
  TPR memakai 129 MAL dalam 98 kampanye; FPR memakai 1.868 TYP dalam 1.865 kampanye.
- Tiga perbandingan per model: DIFF+I → DIFF+I+M; DIFF+I+MM → DIFF+I+MB;
  DIFF+MB → DIFF+I+MB. Invalid dihitung benign, sesuai analisis utama naskah.
- Untuk tiap kampanye, jumlahkan selisih indikator prediksi malicious antara
  konfigurasi B dan A. Satu tanda digunakan bersama untuk seluruh kampanye.
  Statistik adalah jumlah selisih dibagi jumlah pasangan, sehingga sesuai dengan
  selisih TPR/FPR berbobot pasangan yang dilaporkan naskah.
- Distribusi dihitung **eksak** melalui dynamic programming dengan hitungan
  bilangan bulat. Ini menggantikan rencana Monte Carlo 100.000 pengacakan dalam
  draf; hipotesis dan statistik tetap, tetapi tidak ada galat Monte Carlo atau
  seed untuk nilai p. Kedua ekor dan nilai yang sama ekstrem ikut dihitung.
- Koreksi Holm diterapkan sekali pada seluruh **36 hipotesis**
  (6 model × 3 perbandingan × 2 metrik); signifikan jika nilai p terkoreksi < 0,05.
  Tabel naskah membulatkan tiga desimal dan menampilkan nilai < 0,001 sebagai
  `<0.001`; keputusan memakai angka penuh, bukan angka yang dibulatkan.
- Interval bootstrap 95% yang sudah ada tetap dipakai dan tidak dikoreksi
  multipel. Interval tersebut bukan inversi uji permutasi ini: keduanya dapat
  berbeda dalam keputusan, terutama karena distribusi uji diskret.

Uji mengasumsikan kampanye independen dan invariansi distribusi prediksi ketika
label kedua konfigurasi ditukar bersama dalam satu kampanye (atau simetri tanda
selisih kampanye untuk statistik ini). Kesamaan marginal TPR/FPR saja tidak
menjamin asumsi tersebut. Hasil tetap eksploratori karena pengembangan desain
setelah hasil awal diketahui. Tidak signifikan bukan bukti kesetaraan, tidak
menurunnya deteksi, maupun keunggulan atas metode penelitian lain.

Dasar metodologis: [Winkler et al. (2014)](https://pmc.ncbi.nlm.nih.gov/articles/PMC4010955/)
untuk asumsi pembalikan tanda dan ketergantungan berkelompok, serta
[Holm (1979)](https://www.ime.usp.br/~abe/lista/pdf4R8xPVzCnX.pdf)
untuk kontrol family-wise error. Keduanya dicantumkan dalam bibliografi naskah.

## Dampak pada interpretasi

Ada **13 dari 36 pengujian signifikan**, terdiri atas 12 perubahan FPR dan satu
perubahan TPR. Satu-satunya TPR yang signifikan adalah penambahan M pada
Phi-4-mini: +18,60 poin persentase, p Holm = 0,02215; FPR-nya juga naik.

| Perubahan yang perlu diperjelas | Selisih (poin persentase) | p mentah | p Holm | Kesimpulan |
|---|---:|---:|---:|---|
| Qwen3, MM → MB, TPR | +8,53 | 0,00739 | 0,16986 | Tidak signifikan setelah koreksi |
| Phi-4-mini, MM → MB, TPR | −8,53 | 0,05224 | 0,99254 | Tidak signifikan, termasuk sebelum koreksi |
| Phi-4-mini, tambah intent, FPR | −2,57 | 0,04575 | 0,91490 | Tidak signifikan setelah koreksi |
| Qwen2.5-7B, tambah intent, TPR | +10,85 | 0,00838 | 0,18434 | Tidak signifikan setelah koreksi |
| Llama-3.1-8B, tambah intent, TPR | +8,53 | 0,03469 | 0,72848 | Tidak signifikan setelah koreksi |

Penggantian MM → MB signifikan menaikkan FPR pada Qwen3, Qwen2.5-3B, dan
Qwen2.5-7B, serta menurunkannya pada Phi-4-mini. Semua perubahan TPR untuk
perbandingan itu tidak signifikan setelah koreksi. Penambahan intent signifikan
menurunkan FPR pada Qwen3 dan Granite, serta menaikkan FPR pada Qwen2.5-7B dan
Llama; tidak ada perubahan TPR akibat intent yang signifikan setelah koreksi.

## Reproduksi dan berkas

Dari root repositori:

```bash
MPLCONFIGDIR=/tmp/intendiff-matplotlib .venv/bin/python scripts/paired_pvalues.py
MPLCONFIGDIR=/tmp/intendiff-matplotlib .venv/bin/python -m unittest discover -s tests -p 'test_paired_pvalues.py' -v
MPLCONFIGDIR=/tmp/intendiff-matplotlib .venv/bin/python -m unittest discover -s tests -p 'test_paper_results.py' -v
```

- `paired-pvalues.csv`: 36 hasil, p mentah/terkoreksi, interval lama, jumlah
  prediksi positif, arah ketidaksetujuan, dan distribusi selisih kampanye.
- `paired-pvalues.json`: hasil lengkap, hitungan eksak penugasan tanda,
  asumsi, audit respons, dan SHA-256 berkas sumber.
- `contrast-rows.tex`: baris tabel hasil yang sudah disalin ke naskah utama.
  Skrip menghitung ulang artefak ini, tetapi tidak menimpa revisi teks naskah.

Enam unit test memeriksa kecocokan dengan enumerasi semua tanda pada contoh kecil,
kesetaraan dengan uji binomial McNemar pada kampanye singleton, perlakuan invalid,
pemeliharaan cluster, penolakan data tidak lengkap/duplikat/error, hitungan
bilangan bulat besar, dan koreksi Holm. Dua test pemeriksaan hasil sebelumnya
juga lulus.

## Pemeriksaan LaTeX

Tabel naskah telah dibandingkan dengan 36 hasil hitung; seluruh isian nilai p
terisi. Persamaan dan tabel telah diperiksa visual melalui kompilasi salinan
sementara. `statistical-sections-preview.pdf` memuat dua halaman hasil pemeriksaan
(metode dan tabel), bukan PDF naskah lengkap. `build-verification.json` mencatat
hash naskah, lingkup pemeriksaan, dan keterbatasannya.

**PDF lengkap belum dapat dikompilasi** karena `labs/latex/figures/workflow.pdf`
dan `labs/latex/figures/architecture.pdf` tidak tersedia. Kedua rujukan gambar
tetap dipertahankan pada sumber asli; hanya salinan di `/tmp` yang memakai kotak
bertuliskan gambar hilang untuk pemeriksaan tata letak. Pada salinan tersebut,
kompilasi berhasil tanpa sitasi atau referensi tidak terdefinisi. Peringatan
format CAS pada judul, kolom L, dan anchor kosong masih ada; tidak ada overfull
baru pada persamaan atau tabel statistik.

Dua masalah build yang sudah ada pada revisi juga diperbaiki: entri Draz yang
duplikat di bibliografi tambahan dihapus karena sudah ada di `cas-refs.bib`, dan
label teks CAS diaktifkan sebagai pengganti thumbnail email yang tidak tersedia.
Paket LaTeX tambahan dipasang pada `/tmp/intendiff-texmf`; perintah build setelah
dua gambar tersedia:

```bash
cd labs/latex
TEXMFHOME=/tmp/intendiff-texmf \
TEXMFVAR=/tmp/intendiff-texmf-var \
TEXMFCONFIG=/tmp/intendiff-texmf-config \
latexmk -pdf -interaction=nonstopmode -halt-on-error intendiff-rag.tex
```
