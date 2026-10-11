# Audit validitas eksperimen D81–D85 — 2 Oktober 2026

**Angka baseline dapat direproduksi, tetapi status ilmiahnya masih eksploratif
dengan label sumber/asumsi benign.** Audit menemukan satu perubahan metadata
hasil yang berhasil dipulihkan persis ke checksum awal. Tidak ada verdict,
respons mentah, label, atau angka metrik yang diubah. Pengembangan UI tidak
dilanjutkan; pekerjaan ini memeriksa eksperimen yang sudah berjalan.

## Cakupan dan hasil pemeriksaan

| Pemeriksaan | Hasil |
|---|---|
| Empat batch baseline D81–D84 | 15.568 respons; masing-masing 3.892, lengkap dan unik dalam batch |
| Setiap model × konfigurasi | 973 pair yang sama: 873 kandidat MAL, 100 TYP |
| Respons mentah → parser → angka laporan | Validitas, verdict, evidence, recall sumber, FPR asumsi TYP, macro recall kampanye cocok |
| Log generasi | 1.946 HTTP 200 per model per batch, cocok dengan jumlah baris |
| Gabungan enam model pada output 2.048 | 11.676 baris persis sama dengan sumber tiga batch, tanpa penghitungan ulang kontrol sebagai inferensi baru |
| DIFF/DIFF+I | Konfigurasi, seed, sampling, batas keluaran/konteks, dan tidak adanya retrieval diperiksa |
| Label sumber masuk prompt melalui metadata | Mengubah label/source/campaign/pred metadata tidak mengubah pesan prompt; bukan bukti bebas memorisasi atau identitas paket dalam kode |
| Intent dari predecessor | 1.005/1.005 profil berhasil dibangun ulang persis dari direktori versi sebelum update, dengan tokenizer Qwen2.5 lokal |
| D85 | Seluruh 160 request direkonstruksi; hash payload, tokenisasi lokal/aktual, parsing, dan audit ID kutipan cocok |
| D85 bobot/tokenizer/input/kode | Semua 29 pin sumber/upstream/model diperiksa, termasuk bobot; dokumen keputusan memakai arsip sebelum D86 |

Jumlah 1.005 profil adalah 973 baseline + 32 dev D85. Sembilan string versi
manifest predecessor memiliki tambahan suffix `+...` dibanding field `before`;
bagian sebelum `+` cocok pada semua sembilan. Perbedaan ini dicatat, bukan
diubah. Rekonstruksi intent memastikan asal input, bukan kebenaran klaim README
atau label keamanan. Audit ini tidak menjalankan kode sampel atau LLM baru.

D81 tidak merekam `max_tokens` pada setiap baris; nilai 512 diperiksa melalui
runner dan protokol yang dipin, serta batas completion aktual. D83/D84 juga
dicocokkan dengan audit token konteks tersimpan. Tidak dilakukan tokenisasi
ulang seluruh baseline; tokenisasi ulang penuh dilakukan untuk 160 request D85.

## Temuan integritas berkas dan pemulihan

Baris pertama `data/evaluation/output-budget-20260929/qwen25.results.jsonl`
memiliki `run_key` yang diawali `Qwen/S`, sedangkan field `model` dan salinan
agregat memuat `Qwen/Qwen2.5-Coder-3B-Instruct`. Perbandingan seluruh 1.946 baris
menemukan **hanya satu field `run_key` berbeda**. Penyebab perubahan tidak diketahui.

- Hash sebelum pemulihan: `fced266cf5f5d40de4292b3b707efa12b717aff7acb353ed3c0cd1b5459dbf86`.
- Hash setelah pemulihan: `85914572dc1c8f2a6ce4e4245d1f3ad16fac6fd131db98a955d3bc6f5403f143`,
  persis sama dengan manifest penyelesaian D82. Hanya string key itu dipulihkan.
- Salinan sebelum pemulihan dan catatan perubahan disimpan di direktori audit.
  Tidak ada regenerasi respons atau perubahan parsing/metric.
- **Pin kontrol D83 sudah menunjuk hash varian `fced...`.** Protokol D83 tidak
  diedit untuk menyembunyikan perbedaan. Pemeriksaan pin tersebut memakai
  salinan historis sebelum pemulihan, dengan lokasi resolusi tercatat pada
  `baseline-audit.json`. Kode perbandingan D83 membaca `results.jsonl` agregat,
  yang tetap utuh; hasil perbandingan tidak berubah.

Sesudah pemulihan, semua entri artefak eksperimen dalam lima manifest cocok.
Tujuh entri dokumen hidup (`README`, `.agent/experiments`, `docs/decisions`) dari
manifest lama berbeda karena dokumen telah berkembang; audit melaporkannya,
bukan menyatakan semua hash dokumen identik. Manifest D85 sendiri tetap cocok.
Verifier lama yang mengasumsikan semua path historis sama dengan dokumen hidup
atau varian berkas sekarang dapat gagal; gunakan resolusi historis yang
tercatat, jangan membekukan ulang atau menghapus manifest lama.

## Mengapa Qwen2.5 terlihat meragukan

Angka yang ditanyakan sebelumnya memang berasal dari batch **512 token**:

| Qwen2.5-Coder-3B | Recall label sumber | FPR TYP asumsi benign | Valid menurut parser |
|---|---:|---:|---:|
| DIFF | 80,64% | 45% | 82,53% |
| DIFF+I | 68,16% | 43% | 70,81% |

Recall turun 109 deteksi positif bersih. Dari jumlah itu, **104** merupakan
selisih pada pasangan yang setidaknya satu responsnya invalid; **5** berasal
dari perubahan verdict ketika kedua respons valid. Ini dekomposisi observasi,
bukan bukti kausal bahwa intent merusak penalaran atau bahwa decoder pasti
memulihkan semua deteksi.

Pola tetap terlihat pada anggaran 2.048:

| Model | Recall DIFF → DIFF+I | Selisih positif bersih MAL | Bagian pasangan invalid | Bagian keduanya valid |
|---|---:|---:|---:|---:|
| Qwen2.5-Coder-3B | 84,54% → 72,05% | −109 | −105 | −4 |
| Qwen2.5-Coder-7B | 92,90% → 67,12% | −225 | −220 | −5 |

Aturan utama `invalid → benign` menjadikan recall ukuran seluruh alur,
termasuk kepatuhan format. Sebagai sensitivitas, bila semua invalid dihitung
malicious, recall 3B DIFF/DIFF+I berubah menjadi 96,45%/97,02% dan FPR menjadi
72%/74%. Itu **bukan angka pengganti yang lebih benar**, melainkan bukti bahwa
kesimpulan sangat dipengaruhi penanganan invalid. Invalid harus tetap dilaporkan.

Masalah evidence terpisah: Qwen2.5-7B menyalin placeholder instruksi
`up to 3 lines copied exactly from the smart-diff` dalam **131/915** respons
valid DIFF dan **141/689** respons valid DIFF+I. Total 272 respons ini lolos
parser tetapi placeholder tersebut bukan bukti kode. Parser historis memeriksa
tipe evidence, bukan dukungan semantik atau pencocokan baris. Kolom valid tidak
boleh ditafsirkan sebagai persentase penjelasan yang benar. Bukti nonverbatim
lainnya tidak otomatis disebut halusinasi karena dapat berupa substring.

## Batas validitas penelitian yang masih terbuka

1. **Belum ada gold manusia.** MAL memakai label sumber, TYP diasumsikan benign;
   32 kandidat HN D85 belum memiliki label independen. Angka baseline adalah
   kecocokan terhadap label sementara, bukan akurasi terverifikasi.
2. **Distribusi kampanye timpang.** Ada 224 klaster MAL; 607/873 sampel berada
   dalam satu klaster (69,53%). Contohnya Qwen3-4B DIFF+I memiliki recall mikro
   63,23%, tetapi rerata recall per kampanye 54,05%. Perlu cap/pemisahan kampanye
   pada desain berikutnya, bukan membuang kampanye setelah melihat prediksi.
3. **Input terpotong.** 326/873 MAL dan 14/100 TYP memiliki diff terpotong.
   Salah prediksi dapat berasal dari bukti yang tidak terlihat; audit tidak
   membuktikan semua perilaku berbahaya tetap tercakup. Subgroup harus dilaporkan.
4. **D85 belum menguji trade-off recall–FPR.** IDS-I, IDS-D, dan VERIFY-I selalu
   benign pada 32 kandidat HN. Nol alarm bukan FPR nol, dan tidak mengesampingkan
   model yang gagal mendeteksi MAL. Delapan dari 96 respons ber-ID hanya mengutip
   header/hunk; keberadaan ID tidak menjamin dukungan semantik.
5. **Belum menguji RAG.** Seluruh baseline hanya DIFF/DIFF+I; card kosong.
   Eksperimen ini belum membuktikan manfaat malicious/benign reference cards,
   keunggulan terhadap paper utama, atau hasil hipotesis penelitian utama.

## Tindakan selanjutnya

**Tidak perlu mengulang semua inferensi hanya karena angka Qwen2.5 turun.**
Respons dan perhitungan bisa ditelusuri, dan satu cacat metadata telah dipulihkan
tanpa mengubah hasil. Yang dapat ditulis sekarang: metode, audit, hasil baseline
eksploratif, sensitivitas invalid, serta keterbatasannya. Klaim peningkatan
akurasi atau efektivitas DIFF+I/RAG masih perlu validasi berikutnya.

Prioritas eksperimen berikutnya adalah kontrol **decoder JSON terstruktur**
pada Qwen2.5 untuk **keduanya, DIFF dan DIFF+I**, dengan prompt/model/input/
anggaran output tetap. Ini menargetkan masalah format yang terukur; jangan
sekaligus mengganti prompt, ukuran model, dan dataset lalu mengatribusikan
perbedaan pada satu faktor. Temuan decoder Qwen3 pada D85 belum membuktikan
hasil yang sama pada Qwen2.5.

Untuk menilai deteksi, gunakan dev campuran dengan label independen dan
pemeriksaan bukti; pisahkan dari test berbasis kampanye. Paket kandidat yang
telah disiapkan bukan label gold. Bekukan protokol, label, dan aturan sebelum
inferensi lanjutan; pertahankan seluruh hasil negatif, invalid, dan skip. Label
manusia dapat diberikan melalui berkas sederhana; pekerjaan frontend/backend
tidak menjadi prasyarat penelitian.

## Reproduksi audit

Artefak: `scratchpad/validity-audit-20261002/`. Ketiga audit dan dekomposisi
membaca data eksperimen tanpa mengubah hasil; hanya menulis laporan audit.

```bash
.venv/bin/python scratchpad/validity-audit-20261002/audit.py
.venv/bin/python scratchpad/validity-audit-20261002/audit_dev.py
.venv/bin/python scratchpad/validity-audit-20261002/audit_inputs.py
.venv/bin/python scratchpad/validity-audit-20261002/transitions.py
```

`restoration.json` menjelaskan pemulihan satu key dan hash salinan sebelum/sesudah.
`baseline-audit.json`, `dev-audit.json`, `input-audit.json`, dan
`intent-transitions.json` menyimpan temuan terstruktur, termasuk perbedaan hash
dokumen dan varian historis. Tidak ada bukti anotasi manusia yang dibuat oleh audit.
