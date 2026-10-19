# Akuisisi tambahan MAL, 16 Oktober 2026

Permintaan pengguna: menambah MAL dan memberi tahu bila unduhan membutuhkan
bantuan. **Belum ada unduhan yang membutuhkan bantuan pengguna.** Akses GitHub,
registry npm dan OSV berhasil. Arsip Guo empat ZIP (~10,6 GiB) dan RogueOne
`44204945-ro.tar.gz` (~1,9 GiB) sudah tersedia; catatan verifikasi lengkap lama
ada di `data/preparation/final-rag-20261014/external-archive-verification.json`.

## Hasil tambahan Datadog

Sumber: [Datadog malicious software packages dataset](https://github.com/DataDog/malicious-software-packages-dataset).
Commit baru `8a74a4c8ee0e1a2927f0419e0710968702ded609`, bertanggal
2026-10-16T08:25:21Z. Metadata sumber disimpan terpisah di
`data/upstream/datadog-20261016/`, sumber lama tidak ditimpa.

| Tahap | Hasil |
|---|---:|
| Versi compromised npm dalam inventaris lama | 1.438 |
| Versi compromised npm dalam inventaris baru | 1.443 |
| Target baru diunduh dan cocok Git blob + SHA-256 | 5/5 |
| Ekstraksi target cocok identitas package | 5/5 |
| Pendahulu berhasil diunduh dan diverifikasi integrity registry | 5/5 |
| Pair lolos pemeriksaan pendahulu/advisory | 4 |
| Pair lolos pemeriksaan nama, paparan, dan kampanye | 3 |
| Kampanye baru menurut aturan clustering | **1** |
| Test tambahan dirilis / inferensi tambahan | **Belum / 0** |

Tiga calon pair berasal dari `@memtensor/memos-cloud-openclaw-plugin`:

| Sebelum | Sesudah | Label target |
|---|---|---|
| 0.1.21-beta.0 | 0.1.21 | MAL sumber |
| 0.1.22 | 0.1.23 | MAL sumber |
| 0.1.24 | 0.1.25 | MAL sumber |

Ketiganya berbagi advisory `MAL-2026-16476`, sehingga dihitung satu kampanye.
Pendahulu dipilih dengan aturan semver dan waktu publikasi lama, termasuk
prerelease jika itulah pendahulunya. Tidak adanya advisory pada pendahulu
merupakan hasil screening; bukan gold benign buatan manusia.

Eksklusi:

- `tensorlake@0.5.144`: pendahulu `0.5.143` memiliki advisory malicious
  `MAL-2026-17650`. Tidak mengganti pendahulu dengan versi lebih jauh demi
  meloloskan pasangan ini.
- `@subql/common@5.8.3`: skor Dolos 0,6041397153945667 terhadap material
  `coa@2.0.3` menghubungkannya ke klaster lama `02-echo@0.0.7`. Ini keputusan
  konservatif menurut aturan clustering, bukan pembuktian aktor serangannya sama.

Perbandingan kampanye mewarisi closure D99 **27.536 item**, termasuk tambahan
Guo yang tidak ada pada D96. Semua material baru dibandingkan dengan seluruh
fingerprint lama dan satu sama lain; hash file tambahan nontrivial serta report
MAL tetap digunakan. Semua nama/kampanye pool lama diblok, ditambah nama
dependency pada exposure registry dan test/dev/KB D101 secara eksplisit.
Ambang 0,5 dan batas tiga pair per kampanye tidak berubah.

Artefak otoritatif:

- `data/acquisition/mal-expansion-20261016/datadog/download-summary.json`
- `data/acquisition/mal-expansion-20261016/campaigns-with-exposure/split-proposal.jsonl`
- `data/acquisition/mal-expansion-20261016/campaigns-with-exposure/new-links.jsonl`
- `data/acquisition/mal-expansion-20261016/acquisition-verification.json`
- `data/acquisition/mal-expansion-20261016/pairs.manifest.jsonl`
- `data/acquisition/mal-expansion-20261016/pairs.preprocessed.jsonl`
- `data/acquisition/mal-expansion-20261016/preparation-verification.json`

Direktori `campaigns/` adalah hasil pemeriksaan awal terhadap pool D99 saja;
`campaigns-with-exposure/` menambahkan pemeriksaan eksplisit exposure registry
dan D101. Hasil jumlah sama; gunakan yang kedua.

## Inventaris RogueOne

Seluruh 337.440 entri di layer arsip telah diindeks statis, termasuk pengulangan
antar-layer. Image tidak dimuat atau dijalankan. Indeks berada di
`data/acquisition/mal-expansion-20261016/rogueone/members.jsonl`.

Folder `RO/Samples` berisi BenignSamples, BenignSamples2, RandomBenignSamples,
dan RandomBenignSamples2. Ada fixture pada `RO/tests/dataflow_fixtures`, termasuk
contoh sintetis/sederhana; fixture tersebut tidak otomatis dijadikan MAL nyata
dengan label sumber. **Belum ada tambahan MAL sah dari inventaris RogueOne ini.**
Arsip yang besar tidak membuktikan seluruh corpus MAL paper tersedia di dalamnya.

## Verifikasi dan batas hasil

Audit akuisisi lulus: lima target cocok hash sumber, tiga pair calon cocok
identitas serta metadata, predecessor tree cocok hasil ekstraksi, source label
dan advisory cocok, dan pin input kampanye tidak berubah. Empat tes baru
melindungi pewarisan exposure D99, paparan dependency/test, batas kampanye, serta
inventaris TAR tanpa ekstraksi path/link. Sembilan tes ekspansi lama juga lulus.
Seluruh pembacaan/ekstraksi sampel dan clustering berjalan tanpa jaringan.

Preprocessing akhirnya **3/3 sukses**, tanpa raw fallback. Percobaan pertama
gagal karena modul `tokenizers` belum tersedia di image static-v2. Retry memakai
tokenizers 0.23.2 lokal melalui mount read-only; tidak mengubah sampel atau
normalizer. Tiga baris gagal tetap disimpan bersama tiga baris sukses, sehingga
pembaca wajib mengambil hasil sukses terakhir per ID. Diff masing-masing
4.069 token (0.1.23), 17.817 token (0.1.21), dan 4.445 token (0.1.25).
Hash source tree sebelum/sesudah preprocessing tetap cocok. Image dan
dependensi dicatat di `preparation-verification.json`. Rilis evaluasi tambahan
masih memerlukan protokol terpisah serta audit konteks seluruh konfigurasi/model.

Ini peningkatan **satu kampanye**; belum menyelesaikan kekurangan keragaman MAL.
Test utama tetap 33 MAL. Tambahan ini calon evaluasi terpisah, bukan penyisipan
ke test utama setelah hasilnya diketahui. Kebijakan label sumber D99 tetap;
tidak menambahkan kewajiban anotasi dua manusia. D103 mencatat keputusan ini.
