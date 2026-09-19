# Referensi

Dicek ke sumber asli pada 2026-09-13. **Terverifikasi** berarti judul, penulis,
venue, dan angka yang tercantum di sini sudah dicocokkan ke paper atau halaman
resmi. Yang belum dicek ada di bagian terakhir; periksa dulu sebelum dikutip.

## Referensi utama

**Wyss, E., Tassio, D., De Carli, L., Davidson, D. (2025). Evaluating LLM-Based
Detection of Malicious Package Updates in npm. RAID 2025.**
PDF: https://ldklab.github.io/assets/papers/raid25-llmdetection.pdf

**Data dan kode:** dirilis di OSF (`osf.io/92w4e`). **Publik, tanpa login** —
satu zip 220.605.173 byte, sha256 `8aea1255236fb4753f903a9af165c27f7c2c5723ddcb5610a0cfbdaa82f2150a`.
Daftar isinya sudah dibuka; isi yang mengoreksi paper ada di D56 dan D57.

Fakta yang boleh dikutip:

**Dataset**

- 2.000 typical updates: 1.000 paket yang paling banyak dijadikan dependency + 1.000 paket acak, dari snapshot npm 15 April 2024.
- 46 known malicious updates dari Backstabber's Knife Collection (termasuk coa, rc, ua-parser-js).
- 163 malicious clones dari StacklokLabs. **Hati-hati:** `malicious_clones.txt` di paket replikasi memuat 171 baris (D57).
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
| chalk, debug + 16 paket | September 2025; kredensial maintainer diperoleh lewat rekayasa sosial; payload diam-diam memanipulasi transaksi kripto; gabungan unduhan sekitar 2 miliar per minggu | AWS Security Blog, *Defending against supply chain attacks like Chalk/Debug and the Shai-Hulud worm* (2 Okt 2025) |
| Shai-Hulud | Sepekan setelah chalk/debug (September 2025); berjalan saat post-install, mencuri token npm, PAT GitHub, dan kredensial cloud, lalu menerbitkan versi terinfeksi dari paket lain milik maintainer yang sama; lebih dari 180 paket dalam 24 jam pertama (AWS); varian November 2025 berjalan saat pre-install (Unit 42) | AWS Security Blog; Unit 42, *"Shai-Hulud" Worm Compromises npm Ecosystem in Supply Chain Attack* |
| axios | 31 Mar 2026; akun maintainer dibajak lewat rekayasa sosial; axios@1.14.1 dan axios@0.30.4 menambah dependency `plain-crypto-js` (typosquat `crypto-js`) yang lewat `postinstall` mengunduh dan menjalankan RAT lintas platform | Datadog Security Labs, *Compromised axios npm package delivers cross-platform RAT* |
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

## Tambahan untuk metodologi (dicek 2026-09-13)

| Referensi | Fakta yang dipakai | Bagian di methodology.md |
|---|---|---|
| Wyss et al. 2025 — detail metode | Smart-diff: UglifyJS lalu Webcrack untuk nama berakhiran `js` — `.ts` tidak ikut (D57); Dolos (k-gram 70, window 17) untuk file di kedua versi; `diff` seluruh direktori. Rata-rata smart-diff 25.246 token; 1,47% melebihi 128 ribu token. Prompt role-play "You are a program analyst…". Output diklasifikasi dengan SimCSE + classifier yang dilatih dari 600 output berlabel manual per model. Metrik sensitivity dan specificity. Threat model: penyerang menguasai paket yang awalnya benign dan bisa mengubah isi apa pun. Paket replikasi di OSF berupa satu zip 220.605.173 byte | §3, §4.2, §4.4, §4.5, §6, §11 |
| Guo et al. 2026, arXiv 2603.27549 v2 | 11 kategori perilaku: Command Execution, Data Exfiltration, Data Collection, C2 Communication, Malicious Download, Persistence, Credential Theft, Dynamic Code Execution, File Manipulation, Reverse Shell, Web Injection. 8 teknik evasion: String Obfuscation, Encoding Obfuscation, Code Structure Obfuscation, Silent Error Handling, Hook Abuse, Environment Detection, Anti-Analysis, Trace Cleanup. Data collection dan exfiltration muncul bersama di 4.144 paket | §4.3, §5.1 |
| Zhao, Wallace, Feng, Klein, Singh (2021). *Calibrate Before Use*. ICML | Majority-label bias dan recency bias; urutan contoh bisa mengubah akurasi dari mendekati acak sampai mendekati state of the art | §5.2 |
| Liu, Shen, Zhang, Dolan, Carin, Chen (2022). *What Makes Good In-Context Examples for GPT-3?* DeeLIO | Contoh nearest-neighbor mengungguli contoh yang dipilih acak | §5.2 |
| Min, Lyu, Holtzman, Artetxe, Lewis, Hajishirzi, Zettlemoyer (2022). *Rethinking the Role of Demonstrations*. EMNLP | Mengganti label demonstrasi secara acak hampir tidak menurunkan performa | §5.1 |
| Liu, Lin, Hewitt, Paranjape, Bevilacqua, Petroni, Liang (2024). *Lost in the Middle*. TACL 12:157–173 | Performa tertinggi saat informasi relevan berada di awal atau akhir konteks | §4.5, §6.2 |
| Tam, Wu, Tsai, Lin, Lee, Chen (2024). *Let Me Speak Freely?* EMNLP Industry | Pembatasan format yang ketat (JSON mode) menurunkan kemampuan penalaran, tetapi bisa meningkatkan akurasi klasifikasi | §6.3 |
| Dietterich (1998). *Approximate Statistical Tests for Comparing Supervised Classification Learning Algorithms*. Neural Computation 10(7):1895–1923 | Untuk algoritma yang hanya dijalankan sekali, McNemar adalah satu-satunya uji dengan type I error yang dapat diterima | §11.2 |
| Ohm, Plate, Sykosch, Meier (2020). *Backstabber's Knife Collection*. DIMVA | Sumber 46 insiden Wyss; hanya dilihat dari daftar pustaka Wyss | §3.1 |
| Kong et al. (2024). *Better Zero-Shot Reasoning with Role-Play Prompting* | Dasar role-play di Wyss; hanya dilihat dari daftar pustaka Wyss, paper aslinya belum dibaca | §6 |
| Zahan, Burckhardt, Lysenko, Aboukhadijeh, Williams (2025). ICSE | Daftar penulis lengkap SocketAI | — |

## Dokumentasi resmi (dicek 2026-09-13)

| Sumber | Fakta |
|---|---|
| Model card Qwen3-4B-Instruct-2507 | 4,0B parameter; Apache-2.0; konteks native 262.144 token; hanya mode non-thinking; sampling yang direkomendasikan temperature 0,7, top_p 0,8, top_k 20, min_p 0 |
| `config.json` Qwen3-4B-Instruct-2507 | 36 layer, 32 attention head, 8 KV head, head_dim 128, hidden 2.560, bfloat16, vocab 151.936 |
| Model card Qwen2.5-Coder-3B-Instruct | 3,09B parameter; lisensi `qwen-research`; konteks 32.768 token; 36 layer; 16 query head / 2 KV head |
| `config.json` Qwen2.5-Coder-3B-Instruct | hidden 2.048, bfloat16, vocab 151.936; head_dim tidak tertulis (2.048 ÷ 16 = 128) |
| Engine arguments vLLM (docs.vllm.ai, versi stable) | `--gpu-memory-utilization` default 0,92; `--seed` default 0; `--dtype auto` memakai BF16 untuk model BF16 |
| npm Registry API (github.com/npm/registry) | `GET /-/v1/search` dengan parameter `text`, `size` (maks 250), `from`; `GET /{package}/{version}` memuat `dist.tarball` |
| Dolos | Skor similarity 0–1, dihitung dari proporsi fingerprint k-gram yang sama (winnowing) |
| README GuardDog | Aturan kode sumber berbasis YARA; tidak mengeksekusi kode paket |
| npm Docs, `npm audit` (CLI v11) | Mengirim deskripsi dependensi proyek ke registry dan meminta laporan kerentanan yang sudah diketahui (*known vulnerabilities*) |

## Penelitian terkait tambahan (dicek 2026-09-13, dipakai di Bagian Penelitian Terkait)

| Referensi | Venue | Fakta yang dikutip |
|---|---|---|
| Zimmermann, Staicu, Tenny, Pradel (2019). *Small World with High Risks* | USENIX Security, hlm. 995–1010 | Paket npm secara implisit mempercayai rata-rata 79 paket pihak ketiga dan 39 maintainer; segelintir akun maintainer cukup untuk menyuntikkan kode ke sebagian besar paket |
| Ohm, Plate, Sykosch, Meier (2020). *Backstabber's Knife Collection* | DIMVA; DOI 10.1007/978-3-030-52683-2_2 | 174 paket berbahaya dari npm, PyPI, dan RubyGems, November 2015 – November 2019 |
| Ladisa, Plate, Martinez, Barais (2023). *SoK: Taxonomy of Attacks on Open-Source Software Supply Chains* | IEEE S&P | Attack tree dengan 107 vektor, 94 insiden nyata, 33 safeguard |
| Wyss, Wittman, Davidson, De Carli (2022). *Wolf at the Door* (Latch) | ASIA CCS, hlm. 1139–1153; DOI 10.1145/3488932.3523262 | Manifest izin perilaku saat instalasi yang diperiksa terhadap kebijakan pengguna |
| Duan, Alrawi, Kasturi, Elder, Saltaformaggio, Lee (2021). MalOSS | NDSS | Analisis metadata, statis, dan dinamis; 339 paket dilaporkan, 278 dikonfirmasi |
| Sejfia, Schäfer (2022). *Practical Automated Detection of Malicious npm Packages* (Amalfi) | ICSE, hlm. 1681–1692; DOI 10.1145/3510003.3510104 | Classifier, reproducer, dan clone detector; beberapa detik per paket |
| Huang et al. (2024). DONAPI | USENIX Security | Analisis statis + urutan API dinamis; basis pengetahuan perilaku berjenjang; 325 sampel berbahaya diverifikasi |
| Zhang, Huang, Huang, Chen, Wang, Wang, Peng (2025). Cerebro | ACM TOSEM 34(4); DOI 10.1145/3705304 | Satu model urutan perilaku untuk npm dan PyPI; 196 paket berbahaya baru di npm, 306 di PyPI |
| Zheng et al. (2024). OSCAR | ASE Industry Showcase | Sandbox, fuzzing fungsi yang diekspor, hook API; F1 0,95 (npm); FPR npm turun dari 34,63% ke 2,57% |
| Froh, Gobbi, Kinder (2023). *Differential Static Analysis for Detecting Malicious Updates to Open Source Packages* | SCORED, hlm. 41–49; DOI 10.1145/3605770.3625211 | Kueri CodeQL dibandingkan antarversi; semua versi berbahaya terdeteksi pada dataset riwayat berbahaya; rata-rata 1,3% alarm palsu pada paket npm populer |
| Wang, Li, Qu, Zou, Xu, Xu, Wang, Jin (2025). MalPacDetector | IEEE TIFS 20:6279–6291 | LLM membangkitkan fitur; FPR 1,3%, FNR 7,5%; 39 paket berbahaya baru dikonfirmasi npm |
| Du et al. (2026). Vul-RAG | ACM TOSEM; DOI 10.1145/3797277 | LLM hanya mencapai akurasi 0,06–0,14 saat membedakan kode rentan dari kode tambalan yang mirip; pengetahuan multidimensi menaikkan akurasi 16–24% |
| Kaniewski, Schmidt, Heer (2026). *Revisiting Vul-RAG* | AI&CCPS 2026 (ARES); arXiv 2606.04739 | Replikasi dengan model open-weight; akurasi berpasangan tertahan di sekitar 0,30; kapasitas model saja tidak banyak membantu |
| Ding et al. (2025). PrimeVul | ICSE; DOI 10.1109/ICSE55347.2025.00038 | Model 7B: F1 68,26% pada BigVul, tetapi 3,09% pada PrimeVul |
| Pandita, Xiao, Yang, Enck, Xie (2013). WHYPER | USENIX Security, hlm. 527–542 | NLP untuk menemukan kalimat di deskripsi aplikasi yang menjelaskan kebutuhan izin |
| Qu, Rastogi, Zhang, Chen, Zhu, Chen (2014). AutoCog | ACM CCS; DOI 10.1145/2660267.2660287 | Kesesuaian deskripsi–izin; presisi rata-rata 92,6%, recall 92,0% pada 11 izin; 45.811 aplikasi |
| Guo et al. (2026), benchmark (tambahan) | arXiv 2603.27549v2 | IntelGuard F1 95,98% vs recall SocketAI 44,41%; presisi dan recall alat ditentukan cara alat menyelesaikan ambiguitas capability vs intent |

## Belum diverifikasi

- **Metode statistik standar** yang dikutip tanpa dicek ulang: McNemar (1947), Holm (1979), Wilson (1927), Cohen (1960), Efron & Tibshirani (1993). Detail bibliografinya perlu dicek sebelum dimasukkan ke `cas-refs.bib`.
- **Nama fungsi `statsmodels`** di methodology §11.2, terhadap versi yang dikunci.
- **Venue final Vul-RAG.**
- **Selisih 171 versus 163 malicious clone** di `malicious_clones.txt` (D57).
- **Tanggal commit pertama** repositori kedua model Qwen di Hugging Face, yang dipakai sebagai batas EA3.
- **Artikel StepSecurity tentang node-ipc**, yang baru dilihat lewat ringkasan pencarian.
- Ejaan nama penulis MalPacDetector "Deqing Zou" (sumber ADS menulis "Deiqing"): cek di DBLP.
- DOI Kaniewski et al. (10.1007/978-3-032-35576-8_5) diambil dari judul halaman Springer yang cocok; halamannya belum dibuka.
