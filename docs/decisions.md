# Log keputusan

Setiap entri berisi keputusan, alasan, dan dampaknya.

- Tambahkan entri baru di bawah.
- Jangan hapus entri lama. Kalau sebuah keputusan diganti, tandai dengan "digantikan oleh Dn".
- Setelah Gate G2, setiap perubahan prompt, konfigurasi, daftar capability, atau decision rule wajib dicatat di sini, dan semua konfigurasi dijalankan ulang.

## 2026-09-13 — Audit referensi dan revisi RQ

Konteks: proposal P1 dicek ke sumber asli ([references.md](references.md)).
Hasilnya, desain di [research.md](research.md) dan [experiments.md](experiments.md)
menggantikan RQ di slide 10.

**D1. Wyss et al. (RAID 2025) dijadikan referensi utama.**
- Alasan: tugas dan inputnya sama (smart-diff update), dan kode serta datanya dirilis.
- Dampak: penelitian dibingkai sebagai replikasi dan perluasan, dengan model kecil, intent, dan retrieval contrastive.

**D2. Contoh motivasi di slide 3 diganti** dengan chalk/debug, Shai-Hulud, dan axios.
- Alasan: CVE-2025-66478 adalah kerentanan, bukan update berbahaya.

**D3. Gap 3 diturunkan dari "ide baru" menjadi "pengukuran efek".**
- Alasan: IntelGuard sudah menilai kesesuaian perilaku dengan fungsi paket, dan CHABADA (2014) melakukannya di Android.

**D4. Ditambah RQ1 (deskriptif) untuk Gap 1.**
- Alasan: Gap 1 tidak punya RQ di proposal, dan "apakah model kecil cukup" tidak punya ambang yang terukur.
- Rumusan pembanding eksternal di RQ1 digantikan oleh D23.

**D5. Endpoint utama untuk contrastive dan intent adalah FPR_HN dengan batas recall, bukan F1.**
- Alasan: F1 bergantung pada rasio kelas. Slide 15 sendiri menyebut FPR sebagai metrik primer, sehingga RQ1 lama (F1) tidak konsisten.

**D6. Ditambah kontrol E3-k2** (2 contoh malicious).
- Alasan: E4 berisi 2 contoh dan E3 hanya 1, jadi tanpa kontrol ini efek contrastive tidak bisa dipisahkan dari efek jumlah contoh.

**D7. Ditambah ablation E4-noint dan E0-noint.**
- Alasan: intent ada di semua konfigurasi lama, sehingga RQ2 lama (efek intent) tidak bisa dijawab.

**D8. E1 (fixed 1-shot) dihapus.**
- Alasan: tidak menjawab gap mana pun, dan demo tetapnya berlabel malicious.

**D9. H1 diganti menjadi analisis eksploratif EA1.**
- Alasan: H1 menyebut kelima kategori HN sekaligus, jadi tidak mungkin salah.

**D10. PR-AUC dihapus.**
- Alasan: output model berupa verdict biner tanpa skor.

**D11. Pengulangan run memakai temperature 0,7 dengan 3 seed, hanya untuk E0 dan E4 (EA2).**
- Alasan: pada temperature 0, decoding greedy menghasilkan output yang hampir identik, sehingga 3 seed tidak mengukur apa pun.

**D12. Target data sekitar 250 pair (MAL 50 / HN 100 / TYP 100), dengan minimum per subset dan maksimal 3 pair per kampanye.**
- Alasan: update malicious yang bisa direkonstruksi terbatas; Wyss hanya punya 46 dan RogueOne 41. HN mendapat porsi terbesar karena menjadi endpoint utama.
- Dampak: target n=400 (100/300) di slide 14 tidak berlaku.

**D13. KB dipisah dari test set.** Card malicious diambil dari paket Datadog berkategori malicious intent, dan retrieval mengecualikan card dari paket atau kampanye yang sama.
- Alasan: mencegah kebocoran contoh ke pair yang sedang dinilai, tanpa menghabiskan pair MAL yang jumlahnya sedikit.

**D14. Intent profile diambil dari v_{t−1}.**
- Alasan: pada update yang dikompromikan, penyerang mengendalikan README di v_t.

**D15. Smart-diff wajib menyertakan diff `package.json`.**
- Alasan: payload axios 2026 dan kategori "Trigger Dependency" di Wyss masuk lewat dependency.

**D16. Urutan card E4 di-counterbalance.**
- Alasan: recency bias. Kode saat ini selalu menaruh card benign di posisi terakhir.

**D17. Daftar kategori hard negative dihapus dari system prompt.**
- Alasan: daftar "telemetry, tooling test, lisensi, scraper, deprecation" sama persis dengan kategori HN. Akibatnya FPR_HN absolut menjadi terlalu optimis dan tidak sebanding dengan Wyss.

**D18. Output tidak valid dihitung sebagai `benign` (fail-open), dengan analisis sensitivitas yang menghitungnya sebagai `malicious`.**
- Alasan: kebijakan harus ditetapkan sebelum melihat hasil. Fail-open mengikuti cara RogueOne memperlakukan error.

**D19. Uji konfirmatori dibatasi 6 (H2a, H2b, H3 × 2 model) dengan koreksi Holm, dan bootstrap recall dilakukan per kampanye.**
- Alasan: menghindari klaim dari banyak perbandingan, dan pair dari satu kampanye saling berkorelasi.

**D20. RogueOne tidak dijalankan ulang.**
- Alasan: rata-rata 226,7 detik per update dengan timeout 1 jam, dan membandingkan angka dari dataset yang berbeda tidak sah.
- Dampak: angka RogueOne hanya dikutip sebagai konteks.

**D21. Dokumen konteks dipindah ke `docs/`.**
- Alasan: CLAUDE.md sebelumnya merujuk `.agent/` dan `.ref/`, yang tidak ada di repo. Kalau salah satu anggota tim punya salinan lokal, gabungkan isinya ke `docs/`.
- Status `.agent/` diperbarui oleh D24.

**D22. Posisi penelitian: triage update dependensi sebelum advisory terbit (pelengkap `npm audit`), bukan audit tata kelola TI.**
- Alasan: menyamakan ekspektasi pembaca dan penguji.

## 2026-09-13 — Rumusan RQ1 dan folder `.agent/`

**D23. RQ1 tidak lagi menyebut Wyss et al. dalam rumusannya.**
- Alasan: selisih dengan angka Wyss tidak bisa diuji, karena prompt, implementasi, dan sampelnya berbeda dan GPT-4o tidak dijalankan ulang. RQ yang terikat pada angka satu paper menjanjikan sesuatu yang tidak bisa dibuktikan dengan data sendiri.
- Dampak: perbandingan dengan Wyss, RogueOne, dan IntelGuard pindah ke Diskusi sebagai konteks, tanpa klaim lebih baik atau lebih buruk. Wyss tetap referensi utama dan sumber data.

**D24. Folder `.agent/` dilengkapi sebagai ringkasan kerja untuk agent** (`research.md`, `experiments.md`, `rogueone.md`).
- Alasan: CLAUDE.md merujuk folder ini, dan agent butuh ringkasan operasional (invarian kode, skema file, larangan) yang tidak cocok ditaruh di dokumen penelitian.
- Dampak: `docs/` tetap sumber kebenaran. Kalau isi `.agent/` berbeda dengan `docs/`, `docs/` yang benar dan `.agent/` harus diperbarui.

## 2026-09-13 — Metodologi final

Konteks: seluruh prosedur ditetapkan di [methodology.md](methodology.md). Setiap
keputusan di bawah punya dasar penelitian terverifikasi [R] atau argumen logis
eksplisit [L]; rinciannya ada di bagian yang dirujuk.

**D25. Capability delta tidak ditampilkan ke model; delta hanya menjadi kunci retrieval** (§1).
- Alasan [L]: RQ1 mengukur kemampuan LLM membaca smart-diff. Fitur hasil extractor di prompt membuat hasilnya sebagian milik extractor.
- Alasan [R]: sampel Datadog sebagian besar ditemukan GuardDog, sehingga fitur berbasis aturan tidak setara informasinya antara MAL dan HN.

**D26. Nama paket tidak ditampilkan; perubahan versi tetap ditampilkan** (§1).
- Alasan [L]: mengurangi kemungkinan model mengenali insiden dari namanya.
- Alasan [R]: prompt Wyss et al. juga hanya berisi smart-diff.

**D27. v_{t−1} adalah versi semver tertinggi yang lebih kecil dari v_t dan terbit sebelum v_t** (§2).
- Alasan [R]: ada jalur rilis paralel yang terbit bersamaan (axios@1.14.1 dan axios@0.30.4).

**D28. Kosakata extractor: 8 capability + 2 change signal, dipetakan ke taksonomi Guo et al.** (§4.3).
- `browser_data` ditambahkan. Alasan [R]: 33 dari 46 insiden Wyss adalah form grabbing; Guo et al. punya kategori Web Injection; RogueOne mencatat 22 kasus C-Harvest.
- `env_access` diganti `host_info`, yang tidak menghitung akses variabel bernama. Alasan [L]: membaca variabel bernama seperti `NODE_ENV` adalah konfigurasi rutin.
- Menggantikan daftar capability versi lama di experiments.md.

**D29. Extractor dijalankan pada file mentah, bukan pada smart-diff** (§4.3).
- Alasan [L]: minify/unminify mengubah bentuk kode sehingga pola obfuscation bisa hilang.

**D30. Smart-diff mengikuti spesifikasi Wyss et al.** (§4.2).
- Isi: UglifyJS → Webcrack; Dolos k=70, window 17; `diff` seluruh direktori. Ditambah `diff -ruN` dan pemotongan baris lebih dari 2.000 karakter.
- Data Wyss diambil dari paket replikasi di OSF (satu zip 210 MB, keberadaannya sudah dicek).
- D15 tetap berlaku, karena diff seluruh direktori mencakup `package.json`.

**D31. Konteks 32.768 token untuk kedua model; anggaran smart-diff 28.000 token dengan pemotongan berprioritas** (§4.5).
- Anggaran dihitung dengan tokenizer Qwen2.5-Coder-3B.
- Alasan [R]: batas konteks Qwen2.5-Coder-3B adalah 32.768 token, dan rata-rata smart-diff Wyss 25.246 token.

**D32. Intent profile dibatasi 1.024 token** (§4.4).
- Rincian: description + keywords 128 token, scripts 256 token, sisanya README.
- Alasan [L]: anggaran smart-diff tetap sama di semua konfigurasi.

**D33. Card berisi `intent`, `behavior_chain`, `code_excerpt` (≤ 15 baris), dan `rationale`, dengan total ≤ 512 token** (§5.1).
- Alasan [R]: struktur KB IntelGuard, temuan behavior chain Guo et al., dan temuan Min et al. bahwa label saja kurang berpengaruh.

**D34. Skor seri di retrieval dipecah dengan hash `pair_id|card_id`, bukan urutan KB; retrieval tidak memakai intent** (§5.2).
- Alasan [L]: dengan hanya 10 sinyal, skor seri sering terjadi. Selain itu, E4 dan E4-noint harus mendapat card yang identik.

**D35. Prompt berbahasa Inggris dengan role-play; teks verbatim ada di §6** (§6).
- Susunan pesan: contoh → update → instruksi format.
- Alasan [R]: prompt Wyss berbahasa Inggris dan memakai role-play; Liu et al. (2024) menunjukkan informasi di awal dan akhir konteks lebih terpakai.
- Menggantikan prompt berbahasa Indonesia di `pipeline/prompts.py`.

**D36. Urutan output `evidence → reason → verdict`, tanpa constrained decoding; parsing dengan `raw_decode`; output terpotong dihitung tidak valid** (§6.3, §7).
- Alasan [R]: Tam et al. (2024) menemukan format yang dikunci ketat menurunkan penalaran.
- Alasan [L]: verdict yang ditulis terakhir dipengaruhi bukti yang sudah ditulis.

**D37. Kampanye didefinisikan sebagai laporan yang sama, file identik, atau similarity Dolos ≥ 0,5, dengan penutupan transitif** (§3.6).
- Alasan [L]: kebocoran data lebih merusak validitas daripada berkurangnya n, jadi ambang dibuat condong ke penggabungan.

**D38. Seleksi data deterministik** (§3).
- Seed 2026 dan urutan hash `nama@versi`.
- TYP diambil 50/50 dari dua kelompok Wyss.
- HN dikumpulkan lewat jalur A + B; 125 dikurasi lalu dibagi 100 untuk test dan 25 untuk KB.
- KB malicious 50 card, round-robin per capability, maksimal 2 per kampanye.
- Alasan [L]: urutan hash tidak berkorelasi dengan popularitas atau kemudahan kasus, sehingga pemilihan tidak bisa diarahkan.

**D39. Dev set 10 pair (4 clone Wyss, 3 TYP, 3 HN dari bagian KB); satu revisi instruksi format diizinkan jika validitas JSON < 90%** (§3.5, §6.4).
- Alasan [L]: kegagalan format adalah noise pengukuran, sedangkan aturan keputusan tidak boleh disetel.

**D40. Serving vLLM dengan bfloat16 tanpa kuantisasi, `--max-model-len 32768`, dan 3 request warm-up** (§9.2).
- Stage 2 memakai temperature 0,7, top_p 0,8, top_k 20 untuk kedua model. Alasan [R]: rekomendasi model card Qwen3-4B-Instruct-2507.
- Menyempurnakan D11.

**D41. VRAM tidak diukur dari puncak nvidia-smi; yang dilaporkan adalah memori bobot dari log vLLM ditambah KV cache terhitung** (§9.3).
- Alasan [R]: vLLM mengalokasikan memori GPU di awal sesuai `--gpu-memory-utilization` (default 0,92).
- Menggantikan catatan nvidia-smi di CLAUDE.md.

**D42. Urutan card E3-k2 ikut di-counterbalance** (§5.2).
- Card malicious teratas menempati posisi yang sama dengan di E4, jadi E3-k2 dan E4 hanya berbeda pada card kedua.
- Alasan [R] Zhao et al. (2021): posisi contoh memengaruhi prediksi.

**D43. Perangkat lunak statistik dikunci: `statsmodels`, dan bootstrap memakai seed 2026** (§11).
- Alasan [L]: analisis harus bisa diulang dan menghasilkan angka yang persis sama.

## 2026-09-13 — Kendala perangkat keras

Konteks: GPU yang tersedia dicek terhadap kebutuhan memori di
[methodology.md §9.3](methodology.md#93-kebutuhan-memori-dan-cara-mengukurnya).

**D44. GPU yang tersedia (RTX 3060, 12 GiB) tidak cukup untuk Qwen3-4B pada konteks 32.768 token.**

- Perhitungan memakai rumus §9.3, bukan pengukuran: bobot 7,45 GiB + KV cache 4,50 GiB = **11,95 GiB**, sedangkan kartu hanya punya 12,0 GiB total. Sisa itu masih harus menampung aktivasi dan CUDA context (±0,3–0,5 GiB), dan vLLM hanya mengambil ±11,0 GiB dengan `--gpu-memory-utilization` 0,92.
- Qwen2.5-Coder-3B muat: 5,76 + 1,13 = 6,9 GiB, tersisa ±4,4 GiB.
- Alasan [R]: angka bobot dan KV cache diturunkan dari `config.json` kedua model (§9.1).
- **Dampak:** pekerjaan M3–4 (smoke test dev set, parsing, pemotongan diff, pengecualian retrieval) bisa jalan di GPU ini dengan Qwen2.5-Coder-3B. Stage 1 dan Stage 2 tidak bisa.

**D45. Pilihan penyelesaian D44 harus ditetapkan sebelum Gate G2.** Belum diputuskan.

- **Opsi A — jalankan M5–6 di GPU ≥16 GB.** Desain §4.5 dan D31 tidak berubah. Beban: ±6.500 panggilan sekuensial (3.500 Stage 1 + 3.000 Stage 2) dengan prompt rata-rata ±25 ribu token, perkiraan kasar 2–3 hari GPU menyala. Runner sudah resumable, jadi boleh dicicil.
- **Opsi B — turunkan `--max-model-len` ke ±20.480 token.** Qwen3-4B jadi muat di 12 GiB, tetapi anggaran smart-diff §4.5 turun dari 28.000 ke ±15.700 token. Karena rata-rata smart-diff Wyss 25.246 token [R], mayoritas pair akan terpotong, bukan sebagian. D31 mewajibkan kedua model menerima input identik, jadi Qwen2.5-Coder-3B harus ikut diturunkan meski muat.
- **Opsi C — kuantisasi.** Ditolak: melanggar D40.
- Alasan [L]: `truncated` sudah menjadi subgroup analysis, jadi memperbanyak pemotongan justru mengaburkan hal yang sedang diukur. Opsi A menukar biaya sewa dengan validitas; Opsi B menukar validitas dengan biaya.
- **Dampak:** setelah G2 desain beku, sehingga mengubah panjang konteks memaksa seluruh konfigurasi dijalankan ulang. Kalau Opsi B dipilih, §4.5 harus diturunkan ulang dan dicatat sebagai keputusan tersendiri.

**D46. Ollama bukan pengganti vLLM; hanya untuk smoke test mekanik.**

- Alasan [R]: Ollama menyajikan model terkuantisasi (GGUF) secara bawaan, sedangkan D40 mensyaratkan bfloat16 tanpa kuantisasi supaya tingkat kuantisasi tidak menjadi faktor pembeda antar konfigurasi.
- Alasan [R]: §9.3 membaca memori bobot model dari log vLLM, yang tidak disediakan Ollama, dan D41 sudah menutup jalan `nvidia-smi`.
- **Dampak:** angka yang masuk laporan hanya dari vLLM. Docstring `pipeline/runner.py` yang sebelumnya menyebut "vLLM atau Ollama" diperbaiki.
