# Diagnosis FPR dan usulan perbaikan — 1 Oktober 2026

Status: audit deskriptif hasil D82–D84 dan usulan eksperimen; belum perubahan
protokol, anotasi gold, atau bukti efektivitas intervensi. Nol inferensi baru.
Snapshot hasil lama tidak diubah. Reproduksi:
`.venv/bin/python scratchpad/fpr-audit-20261001/audit.py`.

## Temuan terukur

FPR = FP / (FP + TN), bukan ukuran kebenaran informasi atau persentase alarm
yang salah. Penyebut saat ini 100 TYP yang diasumsikan benign berdasarkan
sumber; belum gold manusia. Invalid dihitung benign pada metrik primer.

| Model | FP DIFF | FP DIFF+I | Benign → malicious, keduanya valid | Malicious → benign, keduanya valid | Net melalui invalid |
|---|---:|---:|---:|---:|---:|
| Qwen2.5-Coder-3B | 48 | 49 | 12 | 7 | −4 |
| Qwen2.5-Coder-7B | 65 | 67 | 17 | 11 | −4 |
| Qwen3-4B-Instruct-2507 | 6 | 3 | 1 | 4 | 0 |
| Qwen3-8B | 6 | 3 | 0 | 3 | 0 |
| Phi-4-mini | 13 | 13 | 9 | 11 | +2 |
| Llama-3.1-8B | 57 | 69 | 14 | 3 | +1 |

Hitungan berasal dari seluruh 11.676 respons, dicocokkan menurut model,
konfigurasi, dan pair. Ini menunjukkan efek intent berbeda menurut model.
Llama memiliki net +11 FP pada pasangan valid dan +1 melalui invalid;
kenaikannya tidak dapat dijelaskan hanya oleh masalah JSON. Pemilihan subset
sama-sama valid bersifat deskriptif, bukan estimasi kausal yang bebas bias.

Intent TYP memiliki nilai `not available`/kosong pada description 17/100,
keywords 45/100, scripts 20/100, README 10/100. Kehadiran teks juga tidak
menjamin cakupan semantik; profil sekarang berisi metadata dan kutipan README
versi sebelumnya, belum kontrak perilaku dengan sumber per klaim.

## Contoh alasan model yang diperiksa terhadap smart-diff

Contoh dipilih untuk menjelaskan mekanisme potensial, bukan sampel acak
untuk mengestimasi prevalensi penyebab. Semua berikut Llama benign → malicious
dengan JSON valid. Pembacaan ini tidak menggantikan anotasi independen.

| Pair | Perubahan yang tampak | Masalah pada alasan DIFF+I |
|---|---|---|
| supports-color@9.4.0 | Kondisi GITHUB_ACTIONS diperluas dengan GITEA_ACTIONS | Ketiadaan penyebutan di dokumentasi dijadikan alasan malicious tanpa menunjukkan tindakan berbahaya |
| create-require@1.1.1 | Import URL ditambahkan di create-require.d.ts | Deklarasi tipe dan ketidaksesuaian dokumentasi dijadikan alasan; diff tidak menunjukkan akses jaringan |
| last-match@0.0.3 | Fungsi pencocokan regex dihapus | Alasan menyebut fungsi ditambahkan dan s.match(re) memiliki kemampuan jaringan; tidak didukung diff |
| opex-ngx-pinch-zoom@0.1.1 | Versi dan newline berubah | Alasan menyatakan scripts baru dapat mengeksekusi kode saat install, padahal penambahan scripts tidak ada pada diff |

Ini memberi bukti kesalahan interpretasi diff dan klaim yang tidak berpijak
pada kode, selain hipotesis bias ketidaksesuaian intent. Penjelasan keluaran
model bukan akses ke proses internalnya; belum membuktikan sebab tunggal.

## Intervensi yang layak diuji secara terpisah

1. **Kontrol format pada dev baru.** Gunakan skema JSON terkendali dan ID
   baris sebagai bukti, dengan pemeriksaan ID benar-benar tersedia. Terapkan
   sama pada semua arm baru. Validitas sintaks tidak membuktikan klaim benar.
   Pertahankan hasil historis dan laporkan invalid terpisah beserta sensitivitas.
2. **Verifikasi klaim terhadap perubahan.** Bedakan added/deleted/context,
   runtime/type declaration/test/metadata. Minta bukti pemicu dan tindakan
   berbahaya, data/tujuan bila relevan, serta alasan benign alternatif.
   Klaim di luar bukti harus ditandai tidak diketahui. Jangan menganggap
   semua deklarasi tipe/metadata aman: perubahan metadata dapat mengubah
   entrypoint, dependency, atau lifecycle script. Prioritaskan pemeriksaan
   keterlacakan, bukan menambah peringatan umum: SYSTEM sudah menyatakan API
   sensitif sendiri tidak cukup membuktikan malicious.
3. **Intent terstruktur dan bersumber.** Pisahkan tujuan, operasi yang
   diharapkan, pemicu, data/tujuan, dan informasi yang belum diketahui.
   Ambil dari versi sebelumnya dengan penunjuk sumber. Ketiadaan dokumentasi
   tidak membuktikan penyimpangan berbahaya; kesesuaian tujuan juga tidak
   membuktikan aman. Hindari whitelist berdasarkan nama paket.
4. **Retrieval pembanding benign yang mirip.** Uji DIFF+I+MB melawan
   DIFF+I+MM: sama-sama dua card, namun MB berisi satu malicious dan satu
   benign dengan kapabilitas/pemicu mirip. Label dan rationale harus diverifikasi;
   tidak mengambil paket/kampanye evaluasi ke KB. Ini menguji hipotesis
   utama riset, bukan klaim bahwa RAG sudah terbukti membantu.
5. **Konteks kode terarah bila diperlukan.** Tambahkan fungsi pemanggil dan
   alur data secara statis untuk potongan yang ambigu. Slicing tidak boleh
   membuang kasus gagal/empty dari denominator. Tidak mengeksekusi sampel.

## Urutan evaluasi yang disarankan

- Audit label dan kelompokkan FP serta FN; selesaikan gold TYP/HN dengan
  dua anotator independen. Gunakan 973 pair yang sudah dilihat sebagai bahan
  eksplorasi, bukan holdout baru untuk menyetel lalu mengklaim generalisasi.
- Pisahkan dev, KB, dan holdout berdasarkan paket/kampanye; tambahkan holdout
  yang belum digunakan untuk pemilihan prompt. HN berisi perilaku benign
  yang menyerupai malicious dengan label yang dapat dipertanggungjawabkan.
- Setelah kontrol format tetap, bandingkan DIFF dan DIFF+I; lalu isolasikan
  intervensi verifier, intent terstruktur, dan retrieval satu per satu.
  Pertahankan DIFF+I+MM vs DIFF+I+MB dan DIFF+MB vs DIFF+I+MB untuk RQ utama.
- Prioritaskan Qwen3-4B sebagai model utama dan Llama-8B sebagai pemeriksaan
  lintas keluarga, dengan status pemilihan eksploratif dinyatakan jelas.
- Ukur FPR TYP/HN, recall, macro recall kampanye, JSON valid, biaya/token,
  interval kepercayaan dan perubahan berpasangan. Kriteria penelitian:
  FPR HN membaik tanpa penurunan recall melampaui margin 5 poin persentase,
  mengikuti aturan keputusan yang sudah ditetapkan. Tidak cukup hanya
  melihat estimasi titik atau FPR turun akibat lebih banyak jawaban invalid.

## Dasar literatur

- [Wyss dkk., RAID 2025, §VI-A](https://ldklab.github.io/assets/papers/raid25-llmdetection.pdf)
  mendapati FP pada operasi sensitif, penghapusan besar, dan perubahan
  dependency. Ini mendukung audit perilaku konkret di atas; skor paper
  tidak langsung sebanding dengan dataset dan parser lokal.
- [Guo dkk., studi NPM, v2](https://arxiv.org/html/2603.27549v2)
  membahas ambiguitas kapabilitas dan intent: hook instalasi juga digunakan
  build tool yang sah. Kemiripan API saja tidak memisahkan kedua kelas.
- [Nguyen dkk., code slicing, v3](https://arxiv.org/html/2512.12313v3)
  menguji representasi alur kontrol/data dengan DeepSeek-Coder-6.7B.
  Hasilnya mendukung pengujian konteks terarah, tetapi terbatas pada 2.537
  paket yang menghasilkan slice tidak kosong; tidak menjamin peningkatan
  pada seluruh corpus kita.

Artefak audit: [ringkasan terukur](../scratchpad/fpr-audit-20261001/summary.json)
dan [semua perubahan verdict valid beserta input/alasan](../scratchpad/fpr-audit-20261001/valid-verdict-changes.jsonl).
