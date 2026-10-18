# Build naskah evaluasi berbasis sumber, 18 Oktober 2026

`intendiff-rag.tex` adalah draf Bahasa Indonesia berdasarkan D101/D102/D105.
File hasil eksploratori lama tetap disimpan, tetapi tidak dimuat naskah aktif.
File Inggris yang masih kosong dipertahankan.

Dari root repository, bentuk ulang tabel dan gambar:

```bash
.venv/bin/python pipeline/paper_results.py
.venv/bin/python -m unittest discover -s tests -p 'test_paper_results.py'
```

Exporter memeriksa coverage, duplikasi, identitas respons, confusion matrix kedua
kebijakan invalid, akurasi/BA gabungan, serta biaya token/latensi. CI memakai
analisis D105 yang tersimpan. Tidak menjalankan inferensi atau memilih konfigurasi.
Nilai lengkap dan pin sumber berada di `data/writing/paper-20261018/`.
Jangan mengedit `generated/*.tex` secara manual.

Dengan dependency CAS tersedia:

```bash
cd labs/latex
latexmk -pdf -interaction=nonstopmode -halt-on-error intendiff-rag.tex
```

Build lokal memakai TeX Live 2026, CAS 2.4, pdfLaTeX, BibTeX, latexmk 4.88 dan
STIX. Paket tambahan pada `/tmp/intendiff-texmf`: preprint, makecell, multirow,
colortbl, sttools, xstring, footmisc, stix, moreverb, wrapfig, grfext, upquote,
placeins. Registrasi font memakai environment tree yang sama:

```bash
cd labs/latex
env TEXMFHOME=/tmp/intendiff-texmf \
    TEXMFVAR=/tmp/intendiff-texmf-var \
    TEXMFCONFIG=/tmp/intendiff-texmf-config \
    latexmk -pdf -interaction=nonstopmode -halt-on-error \
    -outdir=../../data/writing/paper-20261018/build intendiff-rag.tex
```

PDF disalin ke `intendiff-rag.pdf`: sembilan halaman, terdiri atas satu halaman
highlights dan delapan halaman naskah/lampiran/referensi. Semua sitasi dan referensi
terdefinisi. Satu warning overfull berasal dari kotak keyword nol-lebar pada
CAS; halaman telah diperiksa visual dan tidak ada teks tabel/gambar terpotong.
Warning tidak disembunyikan dari log. Tree `/tmp` sementara; mesin lain perlu
menyediakan dependency tersebut.

Identitas penulis belum tersedia, sehingga draf memakai mode doubleblind dan
footer “Draf penelitian”. Sebelum pengiriman, lengkapi identitas, afiliasi,
deklarasi kontribusi/pendanaan/konflik kepentingan, venue, serta akses artefak.
Isian faktual tersebut tidak ditebak. Backup naskah lama berada di
`data/writing/paper-20261018/previous/`.
