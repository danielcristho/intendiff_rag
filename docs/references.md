# Referensi

Dicek ke sumber asli pada 2026-09-13. **Terverifikasi** berarti judul, penulis,
venue, dan angka yang tercantum di sini sudah dicocokkan ke paper atau halaman
resmi. Yang belum dicek ada di bagian terakhir; periksa dulu sebelum dikutip.

## Referensi utama

**Wyss, E., Tassio, D., De Carli, L., Davidson, D. (2025). Evaluating LLM-Based
Detection of Malicious Package Updates in npm. RAID 2025.**
PDF: https://ldklab.github.io/assets/papers/raid25-llmdetection.pdf

**Data dan kode:** paper menyatakan semua kode dan data dirilis di OSF
(`osf.io/92w4e`, tautan view-only di §VIII). Isinya belum dibuka.

Fakta yang boleh dikutip:

**Dataset**

- 2.000 typical updates: 1.000 paket yang paling banyak dijadikan dependency + 1.000 paket acak, dari snapshot npm 15 April 2024.
- 46 known malicious updates dari Backstabber's Knife Collection (termasuk coa, rc, ua-parser-js).
- 163 malicious clones dari StacklokLabs.
- Pada 46 insiden asli, 33 adalah form grabbing (19 di antaranya obfuscated).

**Metode**

- Smart-diff mereduksi ukuran input sebesar 95,4%.
- Model yang diuji: GPT-4o, GPT-4-Turbo, Gemini-2.0-Flash.

**Hasil deteksi**

- Semua model mendeteksi 46/46 update malicious dan 163/163 clone.
- False positive pada 2.000 typical updates: GPT-4o 8, GPT-4-Turbo 16, Gemini-2.0-Flash 75.
- Rata-rata waktu query GPT-4o 9,91 detik.

**False positive** (Tabel VI) terbagi tiga kategori:

- Sensitive operations.
- Large deletions, termasuk placeholder deprecation yang ditandai oleh semua model.
- Dependency changes.

Pada live analysis, contoh FP antara lain react-native-bootsplash (validasi
lisensi yang di-obfuscate) dan cdk-assets (unggah ke S3 di test script).

**Temuan lain**

- Live analysis dijalankan 23 Oktober 2024 – 17 Januari 2025.
- Model rentan terhadap obfuscation dataflow ringan dan payload yang dipecah.
- Upaya prompt injection justru ditandai malicious oleh semua model.

## Pendukung (terverifikasi)

| Kutipan | Judul resmi dan venue | Fakta yang boleh dikutip | Dipakai untuk |
|---|---|---|---|
| Guo, Song, Guo, Xu, Liu, Ou, Ge, Liu (2026) | *Bridging Expert Reasoning and LLM Detection: A Knowledge-Driven Framework for Malicious Packages*. WWW '26. DOI 10.1145/3774904.3792083; arXiv 2601.16458. Nama sistemnya IntelGuard | KB berisi 4.420 konteks kode malicious dari 8.024 halaman laporan; **hanya contoh malicious**; menilai kesesuaian perilaku dengan fungsi paket (58% penalaran bertipe functional violation); GPT-4.1-mini; paket utuh, bukan update; npm 98,72% akurasi, 0,20% FPR | Posisi Gap 2 dan Gap 3; E3 = retrieval ala IntelGuard |
| Guo, Chen, Xu, Liu, Kang, Song, Liu, Xu, Sun, Liu (2026) | *How Effective Are NPM Malicious Package Detectors? A Large-Scale Empirical Study*. arXiv 2603.27549 v2 (preprint). Judul v1: *Understanding NPM Malicious Package Detection: A Benchmark-Driven Empirical Analysis* | 6.420 malicious + 7.288 benign; 11 tool / 16 varian (v1: 8 tool / 13 varian); ambiguitas capability vs intent; sumber FP: husky, patch-package, prisma dengan install hook; benchmark di figshare DOI 10.6084/m9.figshare.31869370 | Bukti masalah; kandidat HN |
| Sofaer, David, Kang, Yu, Cao, Yang, Nieh (2024) | *RogueOne: Detecting Rogue Updates via Differential Data-flow Analysis Using Trust Domains*. ICSE 2024. DOI 10.1145/3597503.3639199 | Dataset single-update: 300 benign + 41 rogue (29 dari Backstabber's Knife Collection + 12 lainnya); deteksi 31/41 (75,6%), FP 14/300 (4,7%); rata-rata 226,7 detik per update, timeout 1 jam; artefak di figshare | Pembanding non-LLM; sumber data MAL |
| Zahan et al. (2025) | *Leveraging Large Language Models to Detect npm Malicious Packages*. ICSE 2025. DOI 10.1109/ICSE55347.2025.00146; arXiv 2403.12196 | SocketAI; 5.115 paket (2.180 malicious); GPT-4 precision 99% dan F1 97%; GPT-3 precision 91% dan F1 94% | Related work LLM + npm |
| Nguyen, Ho, Pham, Dang-Thi, Vu, Nguyen, Tran-Truong, Vu (2025) | *Taint-Based Code Slicing for LLMs-based Malicious NPM Package Detection*. arXiv 2512.12313 (preprint; judul berubah antar versi, pakai versi terakhir) | DeepSeek-Coder 6.7B; lebih dari 7.000 paket; akurasi 87,04% pada 2.537 paket; paket utuh | Pesaing terdekat Gap 1 |
| Ryan et al. (2026) | *An Evaluation of Large Language Models for Detection of Malicious Python Packages*. arXiv 2602.16304 (preprint) | 13 LLM; 4.070 paket PyPI; model melewatkan indikator yang membutuhkan konteks atau intent penulis | Opsional, dukungan Gap 3 (ekosistem PyPI) |
| Du et al. (2024) | *Vul-RAG: Enhancing LLM-based Vulnerability Detection via Knowledge-level RAG*. arXiv 2406.11147 | RAG berbasis pengetahuan dari kerentanan dan perbaikannya | Analogi RAG pengetahuan; relevansi lemah |
| Gorla, Tavecchia, Gross, Zeller (2014) | *Checking App Behavior Against App Descriptions*. ICSE 2014. DOI 10.1145/2568225.2568276 | CHABADA; lebih dari 22.500 app Android; menandai 56% malware baru tanpa pola malware | Akar konsep intent mismatch |
| Gao, Das (2024) | *Customizing Language Model Responses with Contrastive In-Context Learning*. AAAI 2024. DOI 10.1609/aaai.v38i16.29760 | Contoh positif dan negatif dalam prompt membantu model memahami apa yang harus dihindari | Akar konsep contoh pembanding |

## Dataset

| Dataset | Catatan penting |
|---|---|
| Datadog malicious-software-packages-dataset (github.com/DataDog/malicious-software-packages-dataset) | Sampel berupa zip terenkripsi dengan password `infected`. Manifest bernilai `null` berarti paket jahat sejak awal: bisa jadi card KB, tidak bisa jadi pair. Manifest berisi daftar versi berarti paket compromised: kandidat MAL |
| OpenSSF malicious-packages | Laporan format OSV; sebagian besar paket jahat sejak awal |
| Data Wyss et al. (OSF) | Sumber MAL (46 update) dan TYP (2.000 update) |
| Benchmark Guo et al. (figshare) | Level paket, bukan update; berguna untuk kandidat HN |
| Artefak RogueOne (figshare) | Sumber MAL tambahan |

## Insiden untuk motivasi

| Insiden | Fakta | Sumber |
|---|---|---|
| chalk, debug + 16 paket | 8 Sep 2025; akun maintainer diambil lewat phishing; payload mengalihkan transaksi kripto; tersedia sekitar 2 jam | AWS Security Blog; Unit 42 |
| Shai-Hulud | Mulai 15 Sep 2025; worm yang menyebar sendiri lewat `postinstall`; lebih dari 500 paket dihapus | Unit 42 |
| axios | 31 Mar 2026; axios@1.14.1 dan axios@0.30.4 menambah dependency trojan yang memasang RAT | Datadog Security Labs |
| node-ipc | 14 Mei 2026; versi 9.1.6, 9.2.3, 12.0.1 berisi pencuri kredensial obfuscated | StepSecurity (hanya dilihat lewat ringkasan pencarian; baca artikelnya sebelum dikutip) |
| CVE-2025-66478 | Kerentanan RCE (React2Shell) di Next.js, digabung ke CVE-2025-55182. **Bukan update berbahaya** | nextjs.org/blog/CVE-2025-66478 |

URL insiden:

- https://aws.amazon.com/blogs/security/defending-against-supply-chain-attacks-like-chalk-debug-and-the-shai-hulud-worm
- https://unit42.paloaltonetworks.com/npm-supply-chain-attack/
- https://securitylabs.datadoghq.com/articles/axios-npm-supply-chain-compromise/
- https://www.stepsecurity.io/blog/node-ipc-npm-supply-chain-attack

## Koreksi terhadap slide P1

| Slide | Tertulis | Seharusnya |
|---|---|---|
| 3 | CVE-2025-66478 sebagai contoh masalah | Kerentanan, bukan update berbahaya. Ganti dengan chalk/debug, Shai-Hulud, atau axios |
| 5 | Guo et al.: "evaluasi pada 13 tools" | v2: 11 tool / 16 varian (v1: 8 tool / 13 varian) |
| 18 [2] | "IntelGuard: A Knowledge-Driven Framework for Malicious Packages" | *Bridging Expert Reasoning and LLM Detection: A Knowledge-Driven Framework for Malicious Packages* |
| 18 [3] | "Understanding NPM Malicious Package Detection" | v2: *How Effective Are NPM Malicious Package Detectors? A Large-Scale Empirical Study* |
| 18 [4] | Du et al. (2025) | arXiv diunggah 2024; venue final belum dicek |
| 6, 7 | Angka dan limitasi Wyss et al. | **Sudah benar**, tidak perlu diubah |

## Belum diverifikasi

- **Zhao et al. (2021)**, *Calibrate Before Use: Improving Few-Shot Performance of Language Models*, ICML. Dasar teori recency dan majority-label bias, alasan counterbalancing urutan card E4.
- **Ohm et al. (2020)**, *Backstabber's Knife Collection*, DIMVA. Sumber insiden MAL; cara aksesnya belum dicek.
- Venue final Vul-RAG.
- Isi OSF Wyss et al.: apakah generator smart-diff dan tarball tersedia.
- Daftar penulis lengkap SocketAI.
- Tanggal rilis resmi kedua model Qwen (dipakai sebagai batas EA3).
