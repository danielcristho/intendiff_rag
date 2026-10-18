# Kompilasi naskah hasil eksploratori

`intendiff-rag.tex` memuat `results-exploratory.tex` dan
`discussion-exploratory.tex` untuk hasil D88–D90. Naskah masih draf: metadata
penulis, abstrak, highlights, dan kesimpulan utama belum diisi. Angka di Results
bukan evaluasi konfirmatori RAG.

Dengan dependency template CAS tersedia:

```sh
cd labs/latex
latexmk -pdf -interaction=nonstopmode -halt-on-error intendiff-rag.tex
```

Build 12 Oktober 2026 memakai TeX Live 2026, CAS 2.4, pdfLaTeX, BibTeX,
dan latexmk 4.88. Paket tambahan yang sebelumnya belum tersedia dipasang pada
user tree sementara `/tmp/intendiff-texmf`: preprint (balance), makecell,
multirow, colortbl, sttools, xstring, footmisc, stix, moreverb, wrapfig,
grfext, dan upquote. Charis opsional tidak tersedia; template memakai STIX.
Font map dibuat dengan `updmap-user --force` pada tree sementara.

Perintah build yang berhasil di mesin ini:

```sh
cd labs/latex
env TEXMFHOME=/tmp/intendiff-texmf \
    TEXMFVAR=/tmp/intendiff-texmf-var \
    TEXMFCONFIG=/tmp/intendiff-texmf-config \
    latexmk -pdf -interaction=nonstopmode -halt-on-error \
    -outdir=/tmp/intendiff-latex-d90-final intendiff-rag.tex
```

PDF disalin ke `labs/latex/intendiff-rag.pdf`. Sumber naskah, bibliography,
PDF, log build, dan audit penulisan juga diarsipkan dalam
`data/evaluation/granite-dependency-20261012/` dengan checksum.
Build berhasil tanpa sitasi/referensi tak terdefinisi. Peringatan tata letak
pada bagian lama dan daftar pustaka masih ada; PDF merupakan draf penelitian,
bukan naskah siap terbit. Tree `/tmp` bersifat sementara; mesin lain perlu
menyediakan dependency tersebut sebelum build.
