# D88 — Diagnosis konteks dependency bersyarat

Disiapkan 11 Oktober; pembekuan dan inferensi 12 Oktober 2026 (UTC+7).
Direktori tetap `data/evaluation/dependency-context-20261011/` agar jejak persiapan utuh.

Tujuan: menguji apakah akses ke berkas dependency mengubah keputusan IDS-I pada
20 target D87 yang menambahkan `easy-day-js`. Seluruh target ini dinilai benign
oleh IDS-I D87; delapan sebelumnya dinilai malicious oleh SCHEMA-I. Pemilihan
subgroup dan studi ini **post-hoc**, bukan konfirmasi pada holdout.

## Masukan dan kondisi

- Semua 20 target dipertahankan dalam urutan D87; diff dan intent tidak diubah.
- Dua arm: `CTX-1.11.21` dan `CTX-1.11.22`, masing-masing 20 panggilan baru.
  Keduanya memakai prompt IDS-I D87 ditambah instruksi kondisional yang identik.
- Konteks adalah isi verbatim manifest, main entrypoint, dan install hook jika
  ada; bukan seluruh dependency tree. Isi diperiksa terhadap anggota ZIP lokal.
  Tidak menjalankan sampel, lifecycle script, atau menghubungi endpoint sampel.
- Versi 1.11.21 tidak memiliki postinstall; 1.11.22 memiliki
  `postinstall: node setup.cjs --no-warnings`. Keduanya cocok dengan rentang
  `^1.11.21` dan timestamp publikasi arsip mendahului seluruh target.
- Tidak ditemukan lockfile pada arsip 20 target. Versi aktual yang terpasang
  **belum terverifikasi**. Instruksi secara eksplisit meminta penilaian dengan
  asumsi snapshot tersebut yang ter-resolve; tidak mengklaim itu kejadian nyata.
- Label keamanan, advisory, cluster, dan prediksi lama tidak dimasukkan sebagai
  konteks. Manifest asli tetap memuat nama paket: ini tidak anonim terhadap
  reputasi/pretraining. Versi 1.11.21 tidak otomatis diberi gold benign.
- Hasil IDS-I lama (0/20 alarm) hanya kontrol historis. Perbandingan dengan
  kontrol mengubah isi konteks sekaligus instruksi kondisional; tidak mengisolasi
  efek jumlah informasi saja. Perbandingan kedua arm baru memakai instruksi sama.

## Inferensi dan audit

Qwen3-4B-Instruct-2507, revisi dan seluruh bobot dipin sama dengan D87; BF16,
temperature 0, top_p 1, seed 0, output 2.048, konteks 32.768, KV 6 GiB,
max_num_seqs 1, prefix caching aktif, generation-config vllm. Runtime harus cocok
dengan D87. Tanpa warmup generasi, retry otomatis, truncation baru atau perubahan
prompt di tengah batch. `/tokenize` diperiksa sekali per arm sebelum generasi.

Model, prompt, parser, snapshot sumber, protokol, dan input dibekukan sebelum
panggilan pertama. ID konteks diteruskan sesudah ID diff tanpa collision. Raw
respons, request hash, token, latensi, validitas dan kutipan disimpan; unknown ID
tidak diam-diam memperbaiki verdict. Pemeriksaan ID adalah keterlacakan, bukan
verifikasi semantik. Invalid tetap dilaporkan terpisah dalam denominator 20.

Ukuran hasil yang ditetapkan: jumlah malicious/benign/invalid per arm, transisi
berpasangan, validitas JSON, length truncation, unknown ID, kutipan dependency,
token dan median latensi sesi. Tidak memilih model/prompt setelah hasil diketahui.
Semua hasil termasuk negatif disimpan. Biaya latensi bukan benchmark kausal.

## Batas klaim dan kebocoran retrieval

Ini satu keluarga dependency bersama pada 20 target, walaupun cluster ID target
berbeda. Tidak melakukan inferensi statistik yang menganggap 20 insiden independen.
Tidak mengukur FPR, recall instalasi aktual, manfaat RAG, atau akurasi gold. Label
MAL sumber target tidak menggantikan penilaian manusia. `data/results.jsonl` studi
utama tetap terpisah. Seluruh target tetap dev terpapar; G1/G2 belum selesai.

Audit menemukan 40/40 kombinasi target × versi dependency lolos filter lama
(nama/cluster berbeda). Menyajikan dependency target sebagai contoh KB **berlabel**
dapat membocorkan jawaban. `pipeline/runner.py::eligible` kini juga mengecualikan
nama dependency yang berubah dari `delta_evidence.dependency_change`, serta nama
eksplisit pada `retrieval_exclude_names`. Seluruh 40 kombinasi ditolak filter baru.
Sidecar pengecualian 64 pair D86 disediakan untuk audit; loader belum otomatis
menggabungkan sidecar. Perlindungan 20 target ini memakai metadata yang sudah ada.
Aturan ini belum membuktikan isolasi semua transitive dependency/alias/klon.

Tidak ada card nyata yang telah diverifikasi untuk pengujian MM/MB. Konteks
sumber tanpa label di D88 bukan contoh retrieval berlabel dan tidak dihitung
sebagai pengujian hipotesis utama DIFF+I+MB vs DIFF+I+MM. Snapshot D85/D87 tetap
dipertahankan; perubahan filter hanya berlaku bagi run mendatang.
