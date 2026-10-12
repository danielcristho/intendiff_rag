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

**D47. Kebutuhan memori diukur, bukan diperkirakan: §9.3 kurang menghitung ~2,0 GiB per model.**

- Sumber: log vLLM 0.29.0 pada RTX 3060 saat `--gpu-memory-utilization 0.45` gagal dengan "No available memory for the cache blocks".
- Yang tidak diperhitungkan §9.3: **CUDA graphs 0,37 GiB** dan **overhead runtime 1,67 GiB** (aktivasi, puncak profiling, alokasi non-torch). Angka bobot model sendiri tepat: §9.3 memperkirakan 5,76 GiB, vLLM melaporkan 5,79 GiB.

| Model @ 32.768 token | §9.3 | Terukur | Selisih |
|---|---|---|---|
| Qwen2.5-Coder-3B | 6,92 GiB | **8,96 GiB** | +29% |
| Qwen3-4B-Instruct | 11,95 GiB | **13,99 GiB** | +17% |

- **Dampak pada D44:** kesimpulannya tidak berubah, tetapi marginnya jauh lebih lebar. Qwen3-4B butuh 13,99 GiB, bukan 11,95 GiB, sehingga GPU 16 GB pun terpakai ~88%.
- **Dampak pada D45:** **opsi B praktis gugur.** Di kartu 12 GiB, Qwen3-4B hanya menyisakan 1,55 GiB untuk KV cache, yaitu maksimum **11.286 token** — sedangkan §4.5 saja sudah menganggarkan 28.000 token untuk smart-diff. Menurunkan konteks tidak cukup untuk membuatnya muat; yang tersisa adalah opsi A.
- **Dampak pada RQ4:** angka "memori minimum terhitung" di §9.3 harus memasukkan CUDA graphs dan overhead runtime, atau yang dilaporkan di naskah akan lebih rendah daripada kebutuhan sebenarnya.
- Qwen2.5-Coder-3B tetap muat di kartu ini: butuh fraksi 0,75, dan `.env.example` disetel 0,80.

**D48. vLLM dijalankan dengan `--generation-config vllm`, mengabaikan `generation_config.json` model.**

- Sumber: peringatan vLLM 0.29.0 saat menyajikan Qwen2.5-Coder-3B-Instruct — "Default vLLM sampling parameters have been overridden by the model's `generation_config.json`: `{'repetition_penalty': 1.05, 'temperature': 0.7, 'top_k': 20, 'top_p': 0.8}`".
- Alasan [L]: runner mengirim `temperature`, `top_p`, dan `top_k` secara eksplisit, sehingga ketiganya tertimpa dengan benar. Tetapi **`repetition_penalty` 1,05 tidak pernah dikirim**, jadi nilai itu akan berlaku diam-diam pada seluruh run di kedua stage. §9.2 tidak menyebut `repetition_penalty`, yang berarti nilainya seharusnya 1,0.
- **Dampak:** tanpa flag ini, Stage 1 yang seharusnya greedy murni berjalan dengan penalti pengulangan aktif, dan faktor itu tidak tercatat di mana pun. Hasilnya tetap konsisten antar konfigurasi, jadi perbandingan internal tidak batal, tetapi angkanya tidak bisa direplikasi oleh orang yang mengikuti §9.2 apa adanya.
- Berlaku untuk kedua model, karena keduanya dari keluarga Qwen dan mengirim `generation_config.json` serupa.

**D49. Estimasi memori D47 terverifikasi pada perangkat keras sebenarnya.**

- Qwen2.5-Coder-3B pada `--gpu-memory-utilization 0.80`, konteks 32.768: nvidia-smi melaporkan 9.364 MiB terpakai. Dikurangi ~232 MiB milik desktop, vLLM memakai **8,92 GiB**.
- D47 memperkirakan 8,96 GiB (selisih 0,5%); §9.3 memperkirakan 6,92 GiB (meleset 29%).
- **Dampak:** rumus §9.3 untuk RQ4 harus diperbaiki agar memasukkan CUDA graphs dan overhead runtime. Angka yang dilaporkan di naskah memakai pengukuran ini, bukan rumus lama.

**D50. Header smart-diff memakai label `a/` dan `b/`, tanpa path ekstraksi dan tanpa timestamp** (§4.2).

- Alasan [L] **kebocoran nama paket:** `diff -ruN` mencetak path yang diberikan padanya. Di alur sebenarnya path itu memuat nama paket (`/work/node-ipc/9.2.0/...`), sehingga nama tersebut muncul di header setiap file — melanggar D26. Nama yang muncul di *isi* file tetap dibiarkan, sesuai §1, dan efeknya diukur lewat EA3.
- Alasan [L] **reproducibility:** `diff` menambahkan mtime pada baris `---`/`+++`. Karena mtime mengikuti kapan tarball diekstrak, pair yang sama menghasilkan teks berbeda pada setiap ekstraksi. Itu merusak invarian §4.5 (smart-diff identik di semua konfigurasi dan kedua model) sekaligus pengelompokan kampanye lewat SHA-256 file (§3.6).
- Diverifikasi: mengekstrak pasangan yang sama ke dua lokasi berbeda kini menghasilkan SHA-256 identik, dan `patch(1)` tetap menerima formatnya.

**D51. Nama file README dicocokkan tanpa memperhatikan besar-kecil huruf** (§4.4).

- §4.4 menulis "file `README*` di root". Dibaca harfiah pada filesystem yang peka huruf, pola itu melewatkan `readme.md` huruf kecil — dan itu bukan kasus pinggiran: dari tiga paket asli yang diuji (chalk, ms, node-ipc), **dua memakai huruf kecil**.
- Alasan [L]: melewatkan README berarti pair diberi `intent_available=false` padahal README-nya ada. Dampaknya langsung ke RQ3, karena ablation intent akan membandingkan blok intent yang separuh kosong dengan blok intent yang kosong — bukan yang dimaksud §4.4. Jumlah `intent_available=false` juga dilaporkan, jadi angkanya akan salah.
- **Dampak:** pencocokan memakai awalan `readme` tanpa memperhatikan besar-kecil huruf, diambil menurut urutan nama file bila ada lebih dari satu.

## 2026-09-19 — Node GPU baru

**D52. Eksperimen pindah ke RTX 5080 (16.303 MiB); seluruh angka dari RTX 3060 dibuang.**

- Alasan [L]: RQ4 membandingkan biaya antar model. Kalau Qwen2.5-Coder-3B diukur di satu kartu dan Qwen3-4B di kartu lain, selisihnya tercampur dengan perbedaan perangkat keras dan tidak bisa diurai lagi.
- **Dampak:** run yang sudah ada di 3060 diarsipkan sebagai `data/results.rtx3060.jsonl` dan tidak dipakai. `run_key` tidak memuat perangkat keras, jadi tanpa pengarsipan ini runner akan melewatinya sebagai "sudah selesai".
- **D45 selesai lewat opsi A**, bukan dengan menyewa: kedua model muat di kartu ini, sehingga aturan klaim §5 yang mensyaratkan kedua model berlabel Didukung menjadi bisa dipenuhi.

**D53. Angka memori D47 diukur ulang di Blackwell; koreksinya bertahan.**

| Komponen @32.768 token | RTX 3060 (Ampere) | RTX 5080 (Blackwell) |
|---|---|---|
| Bobot Qwen2.5-Coder-3B | 5,79 GiB | 5,79 GiB |
| CUDA graphs | 0,37 GiB | 0,34 GiB |
| Overhead runtime | 1,67 GiB | 1,95 GiB |
| **Total dengan KV 1,13** | **8,96 GiB** | **9,21 GiB** |

- Diturunkan dari log vLLM pada `--gpu-memory-utilization 0.80`: budget 12,74 GiB dikurangi bobot, graph, dan KV cache terlapor 4,66 GiB.
- Bobot identik antar arsitektur, seperti seharusnya. Yang bergeser hanya graph dan overhead.
- **Dampak:** §9.3 memperkirakan 6,92 GiB, meleset **33%** di kartu ini. Koreksi D47 tetap berlaku dan angkanya diperbarui ke pengukuran Blackwell.

**D54. Reproducibility terikat pada perangkat keras dan versi vLLM, bukan hanya seed.**

- Run fixture yang sama pada model, prompt, dan seed identik menghasilkan verdict berbeda di 3060 dan 5080 (false positive 13/21 menjadi 18/21). Dua faktor berubah bersamaan — arsitektur GPU dan `--generation-config vllm` (D48) — jadi tidak bisa diurai, dan tidak perlu: setelan sekarang yang benar.
- Alasan [L]: pada temperature 0 decoding memang greedy, tetapi vLLM memilih backend attention dan kernel berbeda antar arsitektur. Pergeseran numerik kecil cukup untuk membuat greedy mengambil cabang lain.
- **Dampak:** §9.2 harus menyebut model GPU dan versi vLLM sebagai bagian dari kondisi yang wajib sama untuk mengulang hasil. Mengikuti seed saja tidak cukup, dan ini masuk ancaman validitas.

**D55. `--gpu-memory-utilization` disetel per model, bukan satu angka untuk keduanya: 0,80 untuk Qwen2.5-Coder-3B dan 0,95 untuk Qwen3-4B-Instruct.**

- Sumber: Qwen3-4B pada 0,92 di RTX 5080 gagal start — "4.5 GiB KV cache is needed, which is larger than the available KV cache memory (4.45 GiB)". Kurang 0,05 GiB.
- Flag ini adalah **anggaran total** vLLM, bukan batas KV cache. KV cache adalah sisa setelah bobot, CUDA graph, dan overhead runtime dipotong, dan ketiganya tidak bergantung pada nilai flag — bobot dan graph tetap, overhead diukur saat profiling. Karena itu setiap kenaikan fraksi masuk 1:1 ke KV cache.

| Qwen3-4B @32.768 token | GiB |
|---|---|
| Kartu (16.303 MiB) | 15,92 |
| Anggaran @0,92 | 14,65 |
| Non-KV terukur (bobot + graph + overhead) | 10,20 |
| KV cache tersisa | 4,45 |
| KV cache dibutuhkan (§9.1) | 4,50 |
| Anggaran @0,95 → KV cache | 15,12 → **4,93** |

- Alasan [L] **kenapa bukan menurunkan `--max-model-len`:** saran vLLM sendiri adalah turun ke 32.352 token. Itu melanggar D40 dan memaksa Qwen2.5-Coder-3B ikut turun lewat D31, sehingga run yang sudah selesai harus diulang — demi 0,05 GiB yang bisa didapat gratis dari fraksi memori.
- Alasan [L] **kenapa angkanya boleh berbeda antar model:** D41 melaporkan bobot dari log vLLM ditambah KV cache *terhitung* dari `config.json`, dan keduanya tidak bergantung pada fraksi memori. Latensi RQ4 juga tidak bergeser karena runner sekuensial — satu sequence 32.768 token menempati jumlah blok yang sama berapa pun blok yang tersedia.
- Menyempurnakan D47 dan D53, yang mengukur komponen memori tetapi masih mengasumsikan satu fraksi untuk kedua model.
- **Dampak:** 0,95 menyisakan 0,80 GiB di kartu, jadi GPU harus benar-benar kosong sebelum vLLM dinyalakan. `.env.example` tetap 0,80 karena default modelnya Coder-3B.
- **Terverifikasi di perangkat keras** (vLLM di RTX 5080, `--gpu-memory-utilization 0.95`, konteks 32.768). Bobot, graph, dan KV cache dibaca dari log; overhead runtime adalah sisa anggaran 15,12 GiB setelah ketiganya.

| Qwen3-4B-Instruct @32.768 token | §9.3 | Terukur |
|---|---|---|
| Bobot | 7,45 | **7,64** |
| CUDA graphs | — | **0,34** |
| Overhead runtime | — | **2,23** |
| KV cache terhitung (§9.1) | 4,50 | 4,50 |
| **Total** | **11,95** | **14,71** |

- Fraksi minimum sebenarnya **0,924**, sehingga 0,92 kurang 0,07 GiB — cocok dengan defisit 0,05 GiB yang dilaporkan vLLM, dalam batas pembulatan. Prediksi 4,93 GiB KV cache pada 0,95 meleset 0,02 GiB dari 4,91 GiB terukur.
- Overhead 4B (2,23 GiB) lebih besar daripada Coder-3B di kartu yang sama (1,95 GiB, D53), sesuai dugaan karena aktivasinya lebih besar.
- Log memuat **dua** baris `Graph capturing finished`: 0,34 GiB sebelum KV cache dialokasikan dan 0,16 GiB sesudahnya. Hanya yang pertama yang bisa dipastikan masuk anggaran; apakah 0,16 GiB kedua diambil dari cadangan anggaran atau dari sisa kartu tidak bisa ditentukan dari log saja. Marginnya 0,80 GiB, jadi tidak berpengaruh pada keputusan ini.
- **Dampak pada D44:** dikonfirmasi dengan pengukuran, bukan rumus. Qwen3-4B butuh 14,71 GiB, jadi kartu 12 GiB tidak mungkin dan kartu 16 GiB terpakai 92,4%. §9.3 meleset 23% untuk model ini.

## 2026-09-19 — Paket replikasi Wyss dibuka

**D56. Smart-diff mengikuti `code/smart_diff_generator.py` dari paket replikasi, bukan tafsir atas teks paper** (§4.2).

- Paket replikasi Wyss ternyata **publik di OSF** tanpa login (`osf.io/92w4e`, satu zip **220.605.173 byte**, sha256 `8aea1255…`). Catatan lama "tautan view-only, isinya belum dibuka" keliru. Daftar isi dibaca dari central directory zip lewat range request, tanpa mengunduh keseluruhan.
- Generatornya ada, sehingga syarat di akhir §4.2 ("kalau paket replikasi memuat kode generator, kode itu dipakai") berlaku. Tiga hal berubah:

| | Sebelum | Generator |
|---|---|---|
| Flag diff | `diff -ruN` (3 baris konteks) | **`diff -N -U 0 -r`** (nol konteks) |
| Exclude | tidak ada | **`*.wasm *.md *.map .npmignore LICENSE* license* *.tsbuildinfo package-lock.json yarn.lock`** |
| Cakupan minify | `*.js *.ts *.ejs *.mjs *.cjs` | `file.endswith('js')` — `.ts` **tidak** ikut |

- Alasan [R] **nol konteks:** rata-rata 25.246 token yang dipakai §4.5 sebagai dasar anggaran diukur dengan `-U 0`. Dengan 3 baris konteks, smart-diff kita lebih besar dari asumsi itu dan proporsi pair yang terpotong ikut naik — anggaran dibandingkan dengan angka yang dihasilkan aturan berbeda.
- Alasan [L] **`*.md` dibuang:** README tidak pernah masuk smart-diff Wyss. Dengan `-ruN` tanpa exclude, isi README ikut ke dalam diff, sehingga E4-noint dan E0-noint tetap menerima intent yang justru sedang di-ablasi. Ablation §4.4 tidak mengukur yang dimaksud, dan RQ3 kehilangan artinya.
- Alasan [L] **echo opsi dibuang dari header:** `diff` mencetak opsinya sendiri di setiap baris `diff …`. Generator upstream tidak terkena karena membuang file lewat salinan pohon, bukan `-x`, sehingga headernya pendek. Sembilan pola `-x` menambah ±120 karakter per file ke anggaran §4.5 tanpa isi. Implementasi memakai `-x` lalu menghapus echo-nya, agar hasilnya identik tanpa menyalin pohon.
- Diverifikasi: README, `LICENSE`, dan `yarn.lock` tidak muncul di diff; header kembali `diff -N -U 0 -r a/x b/x`; `patch(1)` masih menerima format nol konteks, jadi invarian D50 bertahan.
- **Belum bisa direproduksi:** langkah Dolos memanggil `node index.mjs`, dan `index.mjs` tidak ikut dirilis. `normalize()` tetap pass-through, sekarang dengan perintah persisnya tercatat di TODO.
- **Dampak:** smart-diff berubah, jadi seluruh run sebelumnya batal. Yang terdampak baru 56 run smoke test di fixture; setelah Stage 1 jalan, perubahan yang sama berarti 3.500 run diulang.

**D57. Angka yang dikoreksi setelah paket replikasi dibuka.**

| | Sebelum | Sebenarnya |
|---|---|---|
| Ukuran zip replikasi | 210.605.173 byte | **220.605.173** |
| Cakupan minify | termasuk `*.ts` | `.ts` tidak ikut |
| `malicious_clones.txt` | 163 clone (dari paper) | **171 baris** |

- `typical_updates_popular.txt` dan `typical_updates_random.txt` masing-masing **1.000 baris**, dan `malicious_updates.txt` **46 baris** — cocok dengan paper. Format tiap baris `path_sebelum,path_sesudah`, dan keduanya menjadi kerangka sampel TYP (§3.2) sekaligus jalur A (§3.3).
- Selisih 171 versus 163 clone **belum ditelusuri**; jangan kutip angka mana pun sebelum jelas.
- `code/openai.key` berukuran 0 byte — placeholder, bukan kredensial yang bocor.

## 2026-09-25 — Audit referensi dan dataset sebelum G2

**D58. Batas EA3 adalah satu tanggal per model, dan lengan pasca-rilis punya target minimum.**

- Dua dokumen mendefinisikannya berbeda: research.md §6 menulis "tanggal rilis diambil dari model card", methodology §11.2 menulis "tanggal commit pertama repositori model di Hugging Face". Keduanya di `docs/`, jadi aturan "docs/ yang benar" tidak menyelesaikannya.
- **Yang dipakai:** tanggal commit pertama repositori model di Hugging Face, yaitu saat bobot pertama kali publik. Tanggal di model card dicatat sebagai pembanding; kalau keduanya berbeda, yang lebih awal menjadi batas dan keduanya dilaporkan.
- Alasan [L]: yang diukur adalah kemungkinan sebuah insiden ikut ke data latih. Yang bisa diamati hanya kapan bobot terbit, jadi tanggal paling awal yang bisa dipastikan adalah batas yang konservatif.
- **Target: minimal 15 pair MAL dari kampanye yang terbit setelah batas kedua model.** Kampanye pasca-rilis dikumpulkan lebih dulu sampai target terpenuhi, baru sisa kuota diisi. Urutan hash di dalam kampanye (§3.1) tidak berubah.
- Alasan [L]: MAL didominasi Backstabber's Knife Collection (2015–2019). Empat insiden pasca-rilis yang sudah tercatat di references.md — chalk/debug, Shai-Hulud, axios, node-ipc — hanya memberi paling banyak 11 pair dengan cap 3 pair per kampanye, sehingga tanpa stratifikasi besar lengan itu diserahkan ke undian.
- Dasar angka 15 [L]: Wilson 95% pada recall 0,8 memberi ±22,7 poin pada n=10 dan ±19,1 poin pada n=15. Lebar itu tetap besar, jadi 15 bukan ambang kecukupan melainkan batas bawah agar arah efeknya masih terbaca. Lebar interval selalu dilaporkan bersama angkanya.
- Cap 3 pair per kampanye **tidak** dinaikkan untuk kampanye pasca-rilis. Itu akan membuat satu insiden mendominasi recall, yang justru alasan cap itu ada.
- **Dampak:** kedua tanggal wajib diverifikasi sebelum G1 dan dicatat di sini. Kalau target 15 tidak tercapai, EA3 dilaporkan dengan n apa adanya beserta lebar intervalnya, dan syarat "arah efek sama pada subset pasca-rilis" di kriteria adopsi (research.md §5) dinyatakan tidak dapat dievaluasi, bukan dianggap terpenuhi.

**D59. Kedua sisi pair dari sumber Wyss diambil dari paket replikasi, bukan registry, dan alur eksklusi dilaporkan per kriteria.**

- §4.1 mengambil versi benign dari `dist.tarball` di registry npm untuk semua sumber. Untuk 46 pair Wyss itu tidak perlu: D57 mencatat setiap baris `malicious_updates.txt` berformat `path_sebelum,path_sesudah`, jadi kedua sisi ada di dalam zip.
- Alasan [L]: mengambil dari registry menambah dua risiko tanpa manfaat. Tarball bisa berbeda dari yang dipakai Wyss (repack atau versi ditarik), dan untuk paket yang di-unpublish seluruhnya v_{t−1} tidak ada lagi. Memakai isi zip membuat masukan kami identik dengan masukan mereka.
- Registry tetap satu-satunya jalur untuk sumber Datadog, OSV, dan RogueOne. Di sumber-sumber itu kriteria (c) §3.1 bisa menggugurkan kandidat karena paketnya sudah hilang dari registry.
- **Alur eksklusi dilaporkan per kriteria** (a, b, c, d, dan cap kampanye), bukan hanya jumlah pair yang gugur karena payload biner seperti sebelumnya.
- **Dampak:** §4.1 dan §3.1 diperbarui. `data/samples.jsonl` mencatat asal tiap tarball (`replication` atau `registry`) di samping checksum. Komponen pengunduh dan ekstraksi belum ada di `pipeline/` dan belum tercatat di checklist experiments.md §4; ditambahkan sebagai item, karena seluruh subset bergantung padanya.

**D60. Kuota HN di-backfill antar kategori, dan jalur B punya aturan berhenti.**

- §3.3 menetapkan kategori dari tujuan yang terdokumentasi, bukan dari sinyal penyaring. Kategori sebuah kandidat karena itu baru diketahui setelah verifikasi, sementara kuotanya per kategori (20 uji + 5 card). Konstruksinya tidak bisa menjamin kuota itu.
- **Aturan:** total HN uji dijaga 100 dan card benign 25. Kategori yang tidak mencapai kuotanya diisi dari kategori yang surplus menurut urutan hash. Komposisi akhir per kategori dilaporkan apa adanya, dan EA1 dibaca dengan n yang tidak sama antar kategori.
- Kategori paling rawan adalah Perizinan: dasarnya satu contoh (react-native-bootsplash pada live analysis Wyss) dan sinyalnya `obfuscation` serta `dynamic_code`, kombinasi yang paling jarang sah sekaligus terdokumentasi.
- **Aturan berhenti jalur B:** pencarian sebuah kategori dihentikan setelah 25 kandidat terverifikasi atau 250 hasil pencarian habis, mana yang lebih dulu. Tanpa batas ini volume unduhnya tidak terbatas (5 kategori × ≤250 hasil × 20 rilis per paket).
- Kuota total tetap 125, tidak dinaikkan. Aturan ini ditulis sebelum G1 supaya bukan penyetelan setelah melihat data.

**D61. E2 dihapus; proporsi label card dihitung tanpa inferensi.**

- E2 (satu card teratas tanpa melihat label) tidak masuk perbandingan konfirmatori mana pun dan tidak pernah diuji. Satu-satunya angka yang dilaporkan darinya adalah proporsi label card yang terambil.
- Alasan [L]: angka itu tidak butuh LLM. Retrieval deterministik — Jaccard atas delta, seri dipecah `sha256(pair_id|card_id)`, dan tidak membaca intent — sehingga label card teratas per pair bisa dihitung langsung dari `pairs.jsonl` dan `kb.jsonl`. E2 memakan 500 panggilan untuk angka yang gratis.
- Alasan [L]: vonis E2 juga tidak bisa diatribusikan. Label card-nya berbeda antar pair, jadi FPR-nya campuran dua mekanisme dan tidak berbeda satu faktor dari konfigurasi mana pun.
- **Dampak:** Stage 1 turun dari 3.500 ke 3.000 panggilan. Proporsi label card dilaporkan sebagai properti retrieval (§3.4), bukan sebagai hasil sebuah konfigurasi.

**D62. ID konfigurasi diganti menjadi semantik.**

| Sebelum | Sekarang | Isi |
|---|---|---|
| E0-noint | `DIFF` | smart-diff saja |
| E0 | `DIFF+I` | + intent |
| E3 | `DIFF+I+M` | + 1 card berbahaya |
| E3-k2 | `DIFF+I+MM` | + 2 card berbahaya |
| E4 | `DIFF+I+MB` | + 1 berbahaya + 1 sah |
| E4-noint | `DIFF+MB` | sama, tanpa intent |

- Alasan [L]: penomoran lama adalah sisa skema yang sudah digantikan. E1 dihapus D8 dan E2 dihapus D61, sehingga tabel konfigurasi memuat dua lubang yang tidak berarti apa pun bagi pembaca. ID baru menyatakan komposisi faktornya, sehingga ketiga kontras konfirmatori terbaca sebagai selisih satu token: `+M`, `MM→MB`, dan `±I`.
- Alasan [L] **kenapa sekarang:** `run_key` memuat nama konfigurasi, dan `data/results.jsonl` belum ada — belum ada satu pun run test-set. Rename setelah Stage 1 berarti 3.000 run hangus.
- Entri D1–D61 di file ini **tidak** ditulis ulang. Log ini bertanggal, jadi entri lama tetap memakai ID yang berlaku saat itu, dan tabel di atas adalah pemetaannya.

**D63. Naskah dibingkai kontribusi, tanpa label RQ.**

- RQ1–RQ4 tetap di research.md sebagai desain internal dan tetap mengikat kode serta skrip analisis. Naskah tidak menyebut "RQ1" dan seterusnya; strukturnya mengikuti daftar kontribusi di Pendahuluan.
- Naskah memang sudah tidak memuat satu pun label RQ (diperiksa 2026-09-25), jadi entri ini mengunci keadaan itu, bukan mengubahnya.
- Alasan [L]: pembaca naskah membutuhkan kontribusi dan endpoint, bukan penomoran internal. Penomoran tetap berguna di `docs/` untuk melacak konfigurasi mana menjawab apa.

**D64. Angka yang harus diverifikasi sebelum masuk naskah.**

- **"163 klon" dikutip dua kali di naskah** (Pendahuluan dan §Data) padahal D57 melarangnya sampai selisih 171 versus 163 jelas. Sampai itu selesai, argumen klon ditulis tanpa angka; argumennya — seluruh klon terdeteksi di evaluasi asli — tidak membutuhkan hitungannya.
- **SocketAI "presisi +16%, F1 +9% dibanding CodeQL"** tidak ada di references.md dan tidak bisa diturunkan dari angka yang tercatat (GPT-4 99%/97%, GPT-3 91%/94%). Ditandai belum terverifikasi.
- **Angka RogueOne-Paranoid (38/41 = 92,7%, FP 120/300 = 40,0%) dan CC-Harvest (10 dari 10) terverifikasi**, dibaca dari PDF pada 2026-09-13, tetapi hanya tercatat di `.agent/rogueone.md`. Itu membalik hierarki `docs/` dan `.agent/`, jadi baris RogueOne di references.md dilengkapi.
- **Bagian statistik naskah tidak memuat satu pun sitasi.** Dietterich 1998, Liu et al. 2024, dan Tam et al. 2024 sudah terverifikasi dan masuk `cas-refs.bib`. Lima referensi klasik — McNemar 1947, Holm 1979, Wilson 1927, Cohen 1960, Efron & Tibshirani 1993 — belum diverifikasi, jadi belum masuk.
- **Tabel §11.3 dihitung ulang dan cocok:** recall 0,9 pada n=50 → [0,786; 0,957]; recall 0,8 → [0,670; 0,888].

## 2026-09-25 — Rantai data dibangun

**D65. Dua berkas perantara masuk skema, dan isolasi §4.1 dijalankan sebagai dua fase.**

- §3 menamai `samples.jsonl`, `pairs.jsonl`, `kb.jsonl`, dan `dev.jsonl`, tetapi tidak ada tempat untuk dua fakta yang tidak bisa diturunkan dari kode: versi mana yang perlu diunduh, dan pair mana yang ada beserta labelnya. Keduanya berasal dari pengumpulan dan pelabelan, jadi masing-masing mendapat berkas: `data/wanted.jsonl` dan `data/pairs.manifest.jsonl`.
- **Dua fase** [R]: §4.1 sendiri sudah memisahkannya — tarball "diunduh di luar container", sedangkan ekstraksi dijalankan di container tanpa jaringan. Karena itu `samples.py fetch` butuh jaringan dan tidak pernah membuka arsip, sementara `samples.py extract` membuka arsip dan dijalankan tanpa jaringan. Modulnya tidak memanggil `docker` sendiri; operator yang menjalankan fase kedua di dalam container.
- **Ekstraksi memperlakukan arsip sebagai bermusuhan** [L]: sampel malicious diasumsikan jahat, dan membuka arsipnya adalah satu-satunya titik di mana isinya menyentuh filesystem. Anggota arsip yang path-nya absolut atau memuat `..` ditolak, begitu pula symlink dan hardlink; hanya berkas biasa dan direktori yang diekstrak. Yang ditolak dilaporkan, tidak dibuang diam-diam.
- **Checksum diverifikasi ulang sebelum arsip dibuka** [L]: fase kedua harus bisa memastikan bahwa yang dianalisis adalah bita yang tercatat di `samples.jsonl`, bukan berkas yang berubah di antara dua fase.
- **Awalan `package/` npm dibuang** [L]: tarball npm menaruh semua berkas di bawah satu direktori teratas, sedangkan extractor, intent builder, dan smart-diff mencari `package.json` di akar direktori versi.
- **Diff dipotong di perakit, bukan di runner** (§4.5): `dataset.py` memanggil pemotongan sekali per pair dan menyimpan hasilnya di `pairs.jsonl`, sehingga semua konfigurasi dan kedua model membaca teks yang sama. Runner tidak pernah memotong ulang.
- **Urutan keluaran `pairs.jsonl`** mengikuti urutan naik SHA-256 dari `name@versi` (§3), sehingga berkasnya tidak bergantung pada urutan manifest.
- Terverifikasi lewat dry run penuh tanpa jaringan: tarball bergaya npm → `samples.jsonl` → `work/` → `pairs.jsonl` → prompt keenam konfigurasi, dengan smart-diff sampai ke prompt dan nama paket tidak muncul di header diff.

**D66. Undian TYP dan jalur A adalah satu pembagian, dengan tiga penafsiran dicatat.**

- §3.2 mengambil 100 TYP dari 2.000 typical update Wyss dan §3.3 menjalankan 1.900 sisanya lewat extractor. Keduanya bagian dari satu pembagian atas daftar yang sama, jadi ditangani satu modul ([pipeline/typical.py](../pipeline/typical.py)) supaya aturan pembagiannya tidak hidup di dua tempat.
- **Undian: urut digest dulu, lalu diacak dengan seed 2026.** Alasan [L]: mengurutkan menurut SHA-256 lebih dulu membuat undian tidak bisa dipengaruhi urutan baris di berkas upstream. Yang dipakai `shuffle`, bukan `sample`, karena §3.2 mengganti TYP yang ternyata punya advisory dengan "hasil undian berikutnya" — aturan itu hanya terdefinisi kalau sisa undiannya berurutan. Sisa itu sekaligus menjadi kolam jalur A.
- **Identitas pair dibaca dari `package.json`, bukan dari path.** Alasan [L]: tata letak direktori di dalam zip replikasi belum diverifikasi; D57 baru memastikan format barisnya `path_sebelum,path_sesudah`. Membaca `name` dan `version` dari manifest membuat jalur A tidak bergantung pada tata letak yang belum pernah dilihat.
- **Keluaran memakai field `signal_categories`, bukan `category`.** Alasan [L]: §3.3 menetapkan kategori dari tujuan yang terdokumentasi, sedangkan sinyal hanya menyaring. Satu delta bisa cocok dengan beberapa kategori — `network` masuk kategori 2 dan 4, `process_exec` masuk 1 dan 4 — jadi nama field harus menyatakan bahwa isinya kandidat, bukan penetapan. Anotator yang menetapkan kategorinya.
- **Penyaringan dijalankan tanpa jaringan,** dan kriterianya hanya "delta tidak kosong". Tiga kriteria HN lainnya — tidak ada advisory, tujuan terdokumentasi, penerbit sama — adalah langkah verifikasi; `has_advisory` sudah ada di `collect.py`.
- Terverifikasi pada skala sebenarnya: 1.000 + 1.000 baris menghasilkan 100 TYP (50 popular, 50 random) dan kolam 1.900 tanpa irisan, dengan undian ulang yang identik. Penyaringan diuji atas enam update sintetis yang memicu kelima kategori plus satu tanpa delta.

**D67. Pemilihan card malicious dan batas ukuran card diimplementasikan; skeleton memisahkan yang otomatis dari yang ditulis anotator.**

- Round-robin §3.4 dijalankan dengan satu kursor per capability. Alasan [L]: setiap penolakan bersifat permanen — kuota kampanye tidak pernah menyusut, paket tidak pernah dilepas, dan kampanye yang dikecualikan tidak pernah kembali — sehingga kursor yang hanya maju sudah benar dan tidak perlu menyapu ulang kolam.
- **Empat field yang ditulis manusia dikeluarkan dalam keadaan kosong:** `intent`, `behavior_chain`, `code_excerpt`, dan `rationale`. Alasan [R]: §5.1 mewajibkan card disusun dari isi paket oleh anotator A dan dicek anotator B, dan card tidak pernah berasal dari output model. Kode hanya boleh menyiapkan slotnya.
- **`drawn_for` dan `dir` dicatat** sebagai metadata: yang pertama membuat round-robin bisa diaudit, yang kedua menunjukkan anotator ke kodenya. Keduanya tidak pernah masuk prompt, sama seperti `id`, `campaign`, `source`, dan `delta`.
- **`fit` menahan 15 baris excerpt lalu anggaran 512 token**, dan yang dipangkas adalah excerpt (§5.1). Pemangkasan **berhenti di satu baris**: excerpt kosong dirender sebagai placeholder `not available`, yang lebih panjang daripada satu baris kode pendek, sehingga pangkasan terakhir justru membesarkan card. Card yang prosa-nya sendiri sudah melebihi anggaran dilaporkan, bukan dipangkas diam-diam.
- **Perenderan card sekarang hanya didefinisikan di `prompts.card_block`,** dipakai bersama oleh prompt dan pemeriksa ukuran. Alasan [L]: kalau formatnya ditulis dua kali, yang diukur bisa berbeda dari yang dilihat model.
- **Koreksi ke `.agent/experiments.md`:** barisnya menyatakan `label` tidak pernah masuk prompt. Untuk pair itu benar, untuk card salah — §5.1 dan §6.2 menampilkan label card, dan justru itu yang membuat contohnya kontrastif. Barisnya dipisah menjadi field pair dan field card.
- Terverifikasi atas kolam 80 paket sintetis dengan 30 kampanye: 50 card, sebaran round-robin 7/7/6/6/6/6/6/6, maksimum 2 card per kampanye, dan dua kampanye MAL test tidak muncul.

**D68. Pembagian HN mengisi kuota card lebih dulu, dan pengisian kekurangan memakai urutan hash global.**

- §3.3 membagi 125 HN terverifikasi menjadi 100 uji dan 25 card benign, berstrata per kategori. Kategori yang dipakai adalah kategori yang **ditetapkan anotator**, bukan sinyal yang menyaring kandidatnya.
- **Kuota card diisi lebih dulu, baru kuota uji.** Alasan [L]: retrieval kontrastif hanya punya pembanding kalau setiap kategori menyumbang setidaknya satu card benign, sedangkan subset uji yang kurang masih bisa ditambal dari kategori lain. Membalik urutannya akan membuat kategori yang tipis — Perizinan adalah yang paling rawan (D60) — kehilangan card-nya justru pada kategori yang paling ingin diuji.
- **Pengisian kekurangan memakai urutan hash atas seluruh sisa**, bukan urutan kategori. Alasan [L]: mengambil sisa kategori 1 lebih dulu hanya karena nomornya kecil adalah bias yang tidak ada dasarnya, dan D60 sendiri menyebut urutan hash.
- **Komposisi akhir per kategori dilaporkan apa adanya.** Pada simulasi dengan kategori Perizinan hanya mendapat 9 kandidat: total uji tetap 100 dengan komposisi 22/25/4/28/21, card tetap 25, dan kategori Perizinan tetap menyumbang 5 card. EA1 karena itu dibaca dengan n yang tidak sama antar kategori.
- **Kandidat tanpa kategori dihitung, tidak ditebak.** Kandidat yang belum diberi kategori oleh anotator tidak masuk kedua kuota, dan jumlahnya dilaporkan.
- **Dev set (§3.5) tidak butuh komponen baru:** isinya 10 pair berbentuk sama, jadi dirakit `dataset.py` dari manifest yang berbeda.

## 2026-09-28 — Akuisisi data asli dan pemeriksaan sumber

**D69. Arsip dan identitas sumber diperiksa sebelum pemilihan dataset.**

- ZIP OSF sudah diunduh dan SHA-256 cocok dengan metadata OSF. Arsip memuat daftar 2.000 typical updates, tetapi tidak memuat kode versi typical. Versi tepat pada daftar diambil dari registry dengan verifikasi integrity, tanpa instalasi paket. Kedua sisi MAL Wyss tetap memakai ZIP sesuai D59.
- Undian D66 memakai identitas kanonis `name@after`, bukan nama direktori lokal. Perubahan lokasi ekstraksi tidak boleh mengubah hasil undian. Entri yang gagal diunduh atau tidak cocok identitasnya dicatat dan diganti mengikuti urutan undian yang sama. Tidak ada output test model yang dilihat.
- Nama sumber `fangrong-xoc` merujuk ke manifest `@fangrong/xoc`; nama sumber dipertahankan sebagai metadata dan pemeriksaan advisory memakai nama kanonis. Versi `stream-combine@2.0.1` dalam arsip tidak berisi kode; pair tersebut tidak dinyatakan tersedia.
- Metadata build SemVer (`+...`) tidak mengubah precedence versi; manifest aslinya tetap dicatat. Mismatch lain tidak diperbaiki dengan tebakan.

**D70. Inventaris Datadog dipatok ke commit, dan kandidat belum berarti label gold.**

- Snapshot sumber: `a9749c044f47563143ee10f600fee290cdeaeef0`. Tree root GitHub terpotong, sehingga inventaris memakai subtree `compromised_lib` dan `malicious_intent` yang tidak terpotong.
- Semua 1.438 versi compromised yang memenuhi inventaris sumber diunduh. Untuk persiapan KB baru 1.000 versi awal menurut hash `name@version` yang diunduh dari 24.324 versi malicious-intent; ini **prefix kolam**, bukan 50 card final atau hasil screening seluruh kolam.
- Pendahulu Datadog diturunkan dari packument registry yang ikut diarsipkan. Urutan prerelease numerik diperbaiki (`beta.10 > beta.2`), tanggal terbit kedua versi wajib tersedia, dan versi pendahulu yang juga tercatat compromised dikeluarkan. Tarball pendahulu tetap diambil dari registry sesuai §4.1.
- Hasil pemeriksaan advisory, identitas, dan ketersediaan disimpan terpisah dari keputusan manusia. `source_label` tidak dipromosikan menjadi `label`; `signal_categories` tidak dipromosikan menjadi kategori HN.

**D71. Dolos kampanye memakai keluaran JSON library yang dikunci versinya.**

- `@dodona/dolos-lib` 3.5.1 dipasang di image preprocessing; k-gram 70 dan window 17. Adapter mengembalikan pasangan ID dan similarity sebagai JSON, sehingga tidak bergantung pada format tabel terminal CLI. Kegagalan alat adalah error, bukan similarity nol.
- Pemeriksaan kode identik yang cukup panjang, input kosong, dan clustering 45 pair MAL Wyss telah dijalankan dengan Dolos sungguhan. Klaster ini masih parsial: gabungan sumber MAL dan kolam KB belum selesai.
- Adapter kampanye ini **tidak** menggantikan `index.mjs` penghapus kode berulang pada smart-diff. Normalisasi §4.2 langkah 1–2 masih belum lengkap; berkas audit saat ini diberi penanda `raw_zero_context_before_normalization`.
- Tidak ada perubahan hipotesis, prompt, decision rule, kewajiban dua anotator, atau pembekuan G2. Tidak ada inferensi test set yang dijalankan dalam akuisisi ini.

**D72. Rekonstruksi preprocessing statis diberi identitas terpisah sebelum G2.**

- `index.mjs` upstream tidak tersedia. Implementasi lokal bernama `static-dolos-exact-v1`; ini rekonstruksi yang dapat diaudit, **bukan klaim reproduksi identik Wyss**. Seluruh pair akan mencatat versi preprocessing dan laporan per file. Belum ada prediksi test set yang terpengaruh.
- Minify memakai UglifyJS `compress=true, mangle=true`, lalu Webcrack unminify. `deobfuscate=false` dan `unpack=false`; sandbox yang mengeksekusi ekspresi dinonaktifkan dengan fungsi yang selalu menolak. Alasannya: aturan proyek melarang eksekusi sampel, sedangkan deobfuscation string-array Webcrack dapat mengevaluasi kode. Ini perbedaan eksplisit dari CLI default upstream.
- Untuk file sumber yang ada di kedua versi, Dolos k=70/window=17 mengusulkan fragmen berulang. Hanya baris lengkap di fragmen dengan teks identik pada kedua sisi yang dihapus. Kemiripan token saja tidak cukup, karena normalisasi identifier/literal oleh detektor kemiripan dapat menyembunyikan perubahan perilaku. Baris batas fragmen dipertahankan. File baru tidak didedup terhadap file lain.
- File yang byte-nya identik dilewati pada kedua sisi; file non-JS tetap mentah (TypeScript boleh didedup, tetapi tidak di-minify). Kegagalan parsing/minify/unminify mempertahankan kedua sisi mentah dan dicatat sebagai fallback. Batas 4 MiB per file sumber berlaku untuk transformasi; file yang lebih besar tetap tersedia mentah, dengan alasan fallback dicatat. Timeout proses menjadikan pair error yang harus ditangani, bukan sukses kosong.
- Input asli tidak diubah. Transformasi bekerja pada direktori temporer di container tanpa jaringan. Capability dan prioritas file tetap dihitung dari sumber mentah.
- Sebelum inferensi, laporan jumlah fallback, pemotongan, dan keterbatasan rekonstruksi harus tersedia. Gate G2 belum dibekukan; hipotesis, enam konfigurasi, dan aturan anotasi tidak berubah.

**D73. Anggaran diff menghitung teks akhir beserta marker pemotongan.**

- Penjumlahan token per hunk tidak menjamin jumlah token teks gabungan, dan marker pemotongan sebelumnya ditambahkan setelah pemeriksaan anggaran. Pemeriksaan akhir sekarang menghitung seluruh string; jika berlebih, hunk paling akhir dilepas sampai muat. Anggaran tetap 28.000 token Qwen, prioritas file dan batas hunk tetap sama. Anggaran nol menghasilkan string kosong, bukan marker yang melampaui anggaran.
- Koreksi diterapkan sebelum batch preprocessing asli dan sebelum inferensi penelitian. Pengujian memastikan teks hasil, termasuk marker, tidak melewati anggaran.

**D74. Penghapusan fragmen tidak menghitung longest-common-substring Dolos.**

- Batch awal `static-dolos-exact-v1` menemukan kegagalan memori pada bundle `pm-controls`. API `Pair` Dolos juga menghitung longest-common-substring dengan biaya kuadratik, padahal normalisasi hanya memerlukan lokasi fingerprint yang cocok.
- `static-dolos-exact-v2` membaca lokasi k-gram dari indeks Dolos langsung, mengelompokkan jendela berdasarkan teks identik, lalu menghapus interior baris lengkap yang sama. Jumlah pasangan jendela yang identik tidak diperbanyak secara Cartesian. Parameter tokenizer/winnowing dan syarat teks identik tetap sama.
- Seluruh batch diulang ke berkas baru dengan versi v2; keluaran v1 tetap disimpan sebagai diagnostik, tidak dicampur dengan hasil v2. Ini koreksi implementasi sebelum G2, bukan perubahan berdasarkan prediksi model.

**D75. Kampanye skala korpus memakai fingerprint Dolos yang dicache.**

- Skor tetap rumus `Pair.similarity` Dolos 3.5.1: jumlah occurrence fingerprint bersama di kedua sisi dibagi jumlah fingerprint kedua sisi. Tidak ada ignored fingerprint atau template. Fingerprint tetap dibuat library Dolos dengan k=70/window=17; hanya perhitungan longest-common-substring yang tidak dibutuhkan dihilangkan.
- Ekuivalensi skor diuji terhadap API `Pair` pada kode identik, rename, perubahan literal, dan kode pendek. Kegagalan fingerprint dicatat dan membuat laporan clustering tidak lengkap; kegagalan tidak boleh menjadi similarity nol.
- Kriteria file identik memakai SHA-256 **byte mentah**, termasuk file biner. Implementasi lama membaca teks sehingga CRLF ternormalisasi dan file biner terlewat. Ini koreksi terhadap definisi §3.6, bukan penggantian kriteria.
- Clustering gabungan saat ini mencakup MAL yang tersedia dan prefix KB yang telah diunduh. Statusnya tetap parsial sampai seluruh pool yang diperlukan serta laporan insiden selesai diverifikasi; tidak dipakai untuk mengklaim 50 card final bebas kebocoran.

**D76. Cache dan pembentukan diff diperbaiki tanpa mengubah teks hasil.**

- Cache normalisasi dipisah menurut isi sebelum/sesudah, jenis parser, versi normalisasi, hash adapter Node, dan lockfile dependensi. Cache menggunakan penggantian berkas atomik; hasil yang dibaca kembali memakai path pair yang sedang diproses. Antrian menyimpan setiap pair yang selesai agar pair lambat tidak menahan checkpoint pair lain.
- Pemisahan raw diff memakai list baris lalu satu `join`, menggantikan penambahan string berulang melalui dictionary yang berbiaya kuadratik. Pemeriksaan 200.000 baris memastikan teks hasil tetap identik. Perubahan ini tidak mengubah smart-diff, anggaran, atau parameter penelitian.
- Manifest kampanye 3,8 GB dibaca secara streaming; kode mentah tidak disimpan seluruhnya dalam RAM setelah fingerprint dihitung. Error resource tetap dilaporkan.

**D77. Runner tidak lagi memilih fixture sebagai pengganti data penelitian yang hilang.**

- Permintaan menjalankan data asli tidak boleh berakhir sebagai panggilan fixture karena `data/pairs.jsonl` belum ada. Runner sekarang memakai path yang diberikan secara literal; fixture hanya bisa dipakai dengan path fixture eksplisit.
- Konfigurasi retrieval menolak KB kosong sebelum membuat hasil atau memanggil model. Ini pemeriksaan kelengkapan masukan, bukan perubahan aturan retrieval saat kandidat setelah pengecualian memang kurang.
- UI audit memakai direktori `data/review/`, terpisah dari dataset final dan hasil model. Label sumber tidak dikirim sebagai gold ke antrean ini. UI menampilkan intent terstruktur, menyimpan evidence verbatim, dan tidak mengambil prediksi untuk pair pending.

## 2026-09-29 — Penutupan batch preprocessing dan batas EA3

**D78. Batas per-model D58 dicatat dari riwayat repositori resmi.**

- Qwen2.5-Coder-3B-Instruct: commit pertama **6 November 2024**, pukul 07:49:38 UTC, [`b16b5ab`](https://huggingface.co/Qwen/Qwen2.5-Coder-3B-Instruct/commit/b16b5abca15f178464c9c85a8f1942f5b925d5ed).
- Qwen3-4B-Instruct-2507: commit pertama **5 Agustus 2025**, pukul 10:58:03 UTC, [`e7974da`](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507/commit/e7974da369bd887ad4f10a072ec4f933ac5391bf). Sufiks `2507` tidak dipakai sebagai tanggal rilis.
- API riwayat masing-masing mengembalikan 16 dan 4 commit tanpa halaman lanjutan. Riwayat, header respons, dan model card diarsipkan dalam `data/upstream/model-release/`; tanggal dan checksum disimpan di `data/acquisition/model-release-cutoffs.json`. Kedua card tidak menyebut tanggal rilis eksplisit yang lebih awal.
- Commit pertama adalah proksi operasional yang dipilih D58; commit awal tidak membuktikan waktu bobot pertama kali dapat diakses publik. Tanggal insiden kampanye tetap perlu diverifikasi dari sumbernya sebelum menetapkan subgroup EA3. Tanggal publikasi versi saja tidak dianggap membuktikan kampanye pasca-rilis.
- Batch 1.157 pair selesai menggunakan `static-dolos-exact-v2`. Pemetaan kampanye 1.870 item yang tersedia ditambahkan sebagai metadata kandidat dengan penanda cakupan prefix KB. Ini tidak membekukan test set, tidak menggantikan anotasi, dan tidak menandai G1/G2 selesai.

**D79. Skeleton card mempertahankan identitas paket untuk pengecualian retrieval.**

- Skeleton malicious sebelumnya menyimpan ID hash card tetapi menghilangkan `name` dan `version`. Akibatnya aturan pengecualian paket sama di `runner.eligible` tidak dapat bekerja dari skeleton yang diisi anotator. Kedua field kini dipertahankan sebagai metadata dan tetap tidak dirender ke prompt.
- Regresi menguji skeleton aktual terhadap pengecualian paket sama serta memastikan identitas tidak masuk teks card. Ini koreksi implementasi sebelum G2; tidak ada perubahan ranking, kuota, atau isi prosa card, dan belum ada hasil penelitian yang terpengaruh.

**D80. Indeks relasi persis dan cache terbatas dipakai untuk pool KB penuh.**

- Semua relasi laporan sama dan SHA-256 file sama digabung melalui indeks sebelum perbandingan Dolos. Penutupan transitif tetap sama; tidak ada perwakilan kampanye yang menggantikan anggota saat perbandingan kode. Cara lama membuat ulang himpunan hash pada setiap pasangan, sehingga biayanya berlebihan untuk 24.324 versi KB.
- Cache skor similarity dibatasi 65.536 pasangan kode. Penggusuran cache hanya menyebabkan penghitungan ulang skor yang sama, bukan pengabaian pasangan atau perubahan ambang.
- Kesetaraan diuji terhadap graf pasangan lengkap pada kasus acak berseed serta urutan terbalik. Pengulangan atas seluruh 1.870 item asli memberi pemetaan dan ringkasan yang identik dengan hasil sebelum optimasi: 714/735 klaster. Parameter Dolos dan definisi kampanye tidak berubah.

**D81. Evaluasi baseline eksploratif dijalankan atas permintaan pengguna untuk memperoleh hasil sekarang.**

- Setelah diberi tahu bahwa anotasi manusia belum tersedia, pengguna meminta: “Oke lanjutkan ke evaluasi untuk mendapatkan resultnya”. Evaluasi yang dapat dijalankan saat ini memakai label sumber; statusnya **eksploratif**, terpisah dari test set konfirmatori §8 dan Gate G1/G2. Kewajiban dua anotator untuk studi utama tidak dinyatakan telah terpenuhi.
- Seluruh 873 kandidat MAL dengan predecessor tersedia/bebas advisory serta 100 TYP digunakan; 2 MAL yang gagal screening dikeluarkan. MAL memakai `source_label`; TYP memakai asumsi benign §3.2. Label sumber tidak ditulis ke paket review manusia. Semua masukan dan hasil eksploratif mencatat asal label serta `human_annotation_verified=false`.
- DIFF dan DIFF+I dijalankan pada kedua model, greedy, seed 0, top_p 1, output maksimal 512 token. Total yang direncanakan adalah 973 × 2 × 2 = 3.892 panggilan. Tidak ada fixture sintetis, pembatasan jumlah pair, atau pemilihan berdasarkan prediksi. Empat konfigurasi retrieval menunggu card yang diverifikasi; HN tidak diberi label berdasarkan sinyal otomatis.
- Dataset ini merupakan kumpulan kandidat yang lolos screening, bukan undian test final dengan cap kampanye dan kuota pasca-rilis. Metrik terhadap label sumber dilaporkan deskriptif. Tidak ada klaim akurasi gold, keputusan hipotesis, hasil HN, atau evidence localization tanpa anotasi. Output tidak boleh dipakai untuk menyetel prompt lalu dilaporkan sebagai hasil konfirmatori pada pair yang sama.
- Kedua model berjalan bergantian pada RTX 5090 yang sama, BF16, konteks 32.768, `max_num_seqs=1`, alokasi GPU 0,65, prefix caching aktif, dan `generation-config=vllm`. Tidak ada request pemanasan terpisah; latency mencakup request awal dan hanya menggambarkan sesi eksploratif ini, bukan benchmark RQ4.
- Artefak berada di `data/evaluation/source-baselines-20260929/`, termasuk snapshot masukan/kode, respons mentah, log server, dan ringkasan. `data/results.jsonl` tetap dicadangkan untuk penelitian utama.

**D82. Eksperimen anggaran keluaran 2.048 token memakai baseline 512 token sebagai kontrol historis.**

- Pengguna menyetujui kelanjutan eksperimen setelah audit Qwen2.5: “Oke lanjutkan experiment tersebut”. Faktor inferensi yang diubah hanya `max_tokens`, dari 512 menjadi 2.048. Tidak ada perubahan prompt, urutan field, parser, aturan invalid-as-benign, atau revisi instruksi format §6.4.
- Seluruh 973 pair D81 digunakan kembali, dengan kedua model dan konfigurasi DIFF/DIFF+I: 3.892 panggilan baru. Baseline 3.892 run pada 512 token dipakai dari artefak yang telah diverifikasi, bukan diulang. Ini kontrol historis dan eksperimen eksploratif setelah hasil awal diketahui, bukan dev/test konfirmatori baru. Hasil tidak menyelesaikan G1/G2 dan tidak digunakan sebagai bukti manfaat RAG.
- Identitas/revisi model, prompt, input, BF16, seed 0, temperature 0, top_p 1, konteks 32.768, urutan pair, prefix caching, GPU utilization 0,65, dan max_num_seqs 1 sama dengan D81. Versi Python dan seluruh library yang dicatat cocok dengan baseline. Prompt terpanjang baseline aktual adalah 29.329 token; batas baru menyisakan minimal 1.391 token konteks. Tidak ada pemotongan input tambahan.
- Sebelum inferensi, snapshot dan checksum dibekukan di `data/evaluation/output-budget-20260929/`. Pengujian payload dengan jaringan dimock memastikan satu-satunya field request yang berubah adalah `max_tokens`; run key dan metadata tambahan membedakan eksperimen. Pemeriksaan ini bukan panggilan evaluasi atau fixture yang dihitung sebagai hasil.
- Metrik yang ditetapkan sebelum inferensi: validitas JSON, respons terpotong, recall label sumber MAL, FPR TYP, sensitivitas invalid-as-malicious, macro recall per kampanye, transisi berpasangan tiga status (malicious/benign/invalid), token, dan latency sesi. Seluruh empat kombinasi dilaporkan, termasuk yang menurun. Kesamaan respons/prefix dengan kontrol historis dicatat untuk diagnosis reproduksibilitas, bukan dipaksakan.
- Tidak ada uji hipotesis utama, anotasi gold, HN, retrieval, atau klaim kausal kecepatan dari perbandingan antar-sesi. Format prompt tidak akan diubah di tengah batch. Data/hasil baseline dipertahankan; checksum `docs/decisions.md` dalam manifest lama merupakan snapshot historis sebelum entri ini ditambahkan, bukan larangan menambah keputusan baru.
- **Penyelesaian 30 September 2026:** 3.892 respons baru unik, seluruhnya HTTP 200, tanpa retry/error transport. Recall label sumber 2.048 token: Qwen2.5 DIFF 84,54% dan DIFF+I 72,05%; Qwen3 DIFF 54,98% dan DIFF+I 63,23%. FPR TYP masing-masing 48%, 49%, 6%, 3%. Total invalid 1.077 → 876; terpotong 520 → 202. Semua recall naik, tetapi FPR Qwen2.5 memburuk. Tidak ada perubahan protokol di tengah batch. Hasil/dekomposisi dan batas interpretasi dicatat di `docs/output-budget-20260930.md`; ini tidak menetapkan 2.048 token sebagai default studi utama atau mengesahkan revisi prompt baru.

**D83. Pembanding eksploratif diperluas ke Qwen2.5-Coder-7B dan Qwen3-8B.**

- Setelah menerima usulan `docs/model-scale-proposal-20260930.md`, pengguna menyatakan “Oke lanjutkan”. Tahap yang dijalankan adalah dua model prioritas: Qwen2.5-Coder-7B-Instruct dan Qwen3-8B, seluruh 973 pair D81/D82, masing-masing DIFF dan DIFF+I; 3.892 panggilan baru. Llama, DeepSeek, Qwen3.5, 14B, fine-tuning, dan konfigurasi retrieval tidak ditambahkan dalam tahap ini.
- Kelompok ukuran operasional: A = 1 ≤ P < 5B dan B = 5 ≤ P < 10B, berdasarkan jumlah parameter total, dengan ukuran per checkpoint tetap dilaporkan. Qwen2.5-Coder-7B adalah 7,61B dan Qwen3-8B 8,2B menurut card resmi. Tidak ada rerata kelompok yang diperlakukan sebagai bukti universal efek ukuran. Qwen3-4B-Instruct-2507 dan Qwen3-8B berbeda checkpoint/post-training; perbandingannya tidak mengisolasi ukuran.
- Revisi model dan checksum bobot/tokenizer dikunci sebelum inferensi dalam `data/evaluation/model-scale-20260930/`. Input, prompt, format, parser, aturan invalid, seed 0, temperature 0, top_p 1, BF16, konteks 32.768, dan output maksimum 2.048 sama dengan D82. Qwen3-8B mendapat `chat_template_kwargs={"enable_thinking": false}` agar mode non-thinking eksplisit. Greedy dipilih sebagai kontrol metode bersama, bukan klaim setting optimal yang disarankan pengembang.
- Model berjalan bergantian pada GPU yang sama, `max_num_seqs=1`, prefix caching aktif, `generation-config=vllm`. Alokasi GPU vLLM dinaikkan dari 0,65 pada kontrol historis ke 0,80 untuk kedua model baru, sebelum inferensi, agar memuat bobot/cache lebih besar. Perbedaan alokasi dan sesi dicatat; latency tidak dipakai sebagai klaim kausal efek ukuran. Tidak ada request pemanasan terpisah.
- Audit tokenisasi lokal atas semua pesan nyata dan pemeriksaan endpoint `/tokenize` tanpa generasi memastikan konteks cukup serta template server sesuai audit. Tidak ada pemotongan input tambahan atau penghapusan pair berdasarkan keluaran model. Jika konteks tidak muat, batch tidak dimulai sampai masalah dicatat dan diselesaikan secara konsisten.
- Kontrol adalah 3.892 hasil D82 pada 2.048 token; tambahan ini menghasilkan tabel empat model × dua konfigurasi, total 7.784 respons historis + baru. Metrik yang dibekukan: recall label sumber MAL, FPR TYP, validitas JSON, jenis invalid, sensitivitas, macro recall kampanye, transisi berpasangan per keluarga, token, dan latency sesi. Semua kombinasi dilaporkan termasuk yang menurun; tidak ada pemilihan prompt/model berdasarkan kenaikan angka.
- Cakupan tetap eksploratif dengan label sumber dan TYP diasumsikan benign, tanpa gold manusia/HN/RAG atau uji hipotesis utama. RQ konfirmatori dan enam konfigurasi inti 3–4B belum diperluas; model lebih besar adalah pembanding tambahan DIFF/DIFF+I. G1/G2 belum selesai. Perubahan desain utama selanjutnya memerlukan pembekuan tersendiri.
- **Penyelesaian 1 Oktober 2026, 00:04 WIB:** 3.892 respons baru unik, seluruhnya HTTP 200, tanpa retry/error transport; 22 checksum snapshot dan 13 checksum kontrol cocok. Qwen2.5-7B DIFF/DIFF+I: recall sumber 92,90%/67,12%, FPR TYP 65%/67%; Qwen3-8B: 50,74%/48,34%, FPR 6%/3%. Dibanding kontrol D82 pada 2.048 token, Δrecall masing-masing +8,36/−4,93/−4,24/−14,89 poin. Invalid baru 435 versus 876 kontrol; terpotong 45 versus 202. Kedua server berhenti normal. Tidak ada perubahan protokol di tengah batch. Seluruh delapan kelompok dan dekomposisi valid/invalid dilaporkan dalam `docs/model-scale-20260930.md`. Tidak ada klaim kenaikan umum akibat ukuran, keputusan hipotesis utama, atau perluasan otomatis ke model lain.

**D84. Eksplorasi diperluas ke dua keluarga model di luar Qwen.**

- Pengguna meminta “oke lanjtukan dengan explore dengan model yang lain”. Tahap ini membandingkan dua model tambahan pada seluruh 973 pair, DIFF dan DIFF+I, target 3.892 inferensi baru; empat model D82/D83 menjadi kontrol historis 7.784 respons pada output 2.048. Tujuannya perbandingan deskriptif lintas keluarga, bukan mencari model sampai hasil positif atau mengisolasi pengaruh ukuran.
- Sebelum melihat prediksi baru, prioritas kecil adalah Microsoft Phi-4-mini-instruct (nominal 3,8B). Prioritas besar: Meta Llama-3.1-8B-Instruct jika akses yang sudah tersedia mengizinkan; berikutnya Mistral-7B-Instruct-v0.3; kemudian IBM Granite-3.3-8B-Instruct dengan `thinking=false`. Pemilihan berdasarkan akses, dukungan runtime, audit semua prompt, dan memori BF16. Tidak ada penerimaan syarat akses baru atau penggantian sumber bobot tidak resmi. Kandidat yang tidak layak dicatat beserta alasannya, bukan dikeluarkan berdasarkan akurasi.
- Audit metadata/tokenizer dilakukan tanpa generasi; checkpoint resmi dipin. DeepSeek-Coder-6.7B turut diperiksa sebagai kandidat terkait literatur, tetapi konteks 16K berpotensi memerlukan eksperimen dengan input pendek yang disamakan untuk semua pembanding. Pair panjang tidak dibuang dan input tidak dipotong hanya untuk satu model. Tidak ada eksekusi kode repository model atau sampel; memakai implementasi runtime lokal dengan `trust_remote_code=false`.
- Input pesan, label sumber, prompt, parser, invalid-as-benign, output 2.048, seed 0, temperature 0, top_p 1, BF16, max_num_seqs 1, prefix caching, dan GPU allocation 0,80 dipertahankan. Template resmi tiap model digunakan. Batas server 32.768 diprioritaskan; 49.152 diperbolehkan hanya jika tokenizer membutuhkan ruang tambahan dan konteks native mendukung, dicatat sebelum inferensi. Ini mempertahankan teks input identik, bukan memaksa jumlah token antar-tokenizer identik. Tanpa RoPE extension, kuantisasi, atau pemotongan input baru. Perbedaan konteks/alokasi/sesi dibatasi interpretasinya pada biaya observasional.
- Snapshot baru di `data/evaluation/model-families-20261001/`; snapshot D82/D83 tetap dipertahankan. Seluruh kombinasi dilaporkan, termasuk yang menurun, dengan recall sumber, FPR TYP, validitas/jenis invalid, sensitivitas, macro recall kampanye, transisi berpasangan, token, dan latency. Tidak ada warm-up LLM sintetis, fine-tuning, revisi format, HN/RAG buatan, atau uji hipotesis konfirmatori. Gold manusia, cutoff temporal formal, serta G1/G2 belum selesai.
- **Hasil seleksi sebelum inferensi:** Phi-4-mini-instruct (3,836B parameter aktual, revisi `cfbefacb99257ffa30c83adab238a50856ac3083`) dan Llama-3.1-8B-Instruct (8,030B, revisi `0e9e39f249a16976918f6564b8830bc894c89659`) lolos akses dan audit 1.946 prompt masing-masing. Keduanya memakai server 32.768; prompt maksimum 29.919 dan 29.186 token. Akses Llama yang tersedia sudah mencukupi tanpa persetujuan syarat baru. Mistral memiliki 109 prompt melebihi konteks native dengan cadangan output; DeepSeek 167. Granite layak secara konteks 49.152 tetapi tidak dipilih karena prioritas Llama sudah memenuhi syarat. Semua audit tanpa generasi disimpan, termasuk kandidat yang tidak dijalankan.
- **Penghentian jawaban native:** `generation-config=vllm` tetap menjaga kontrol sampling. Namun Phi dan Llama memiliki beberapa EOS/end-of-turn pada `generation_config.json` resmi yang tidak seluruhnya terdapat pada `config.json`. Sebelum inferensi, request diberi `stop_token_ids` resmi: Phi `[200020,199999]`, Llama `[128001,128008,128009]`. Ini mencegah model melanjutkan ke giliran berikutnya, tanpa repair respons/parser atau stop string buatan. Daftar dan tokennya diaudit, dicatat dalam metadata setiap respons, serta dipin bersama snapshot. Kontrol Qwen historis tidak memiliki override ini; perbedaan end-of-turn native dicatat sebagai karakteristik lintas keluarga, bukan diklaim identik pada semua field request.
- **Amendemen sebelum prediksi:** startup Phi pertama gagal pada alokasi buffer KV otomatis 15,80 GiB; bobot 7,17 GiB sudah termuat dan belum ada request generasi. Penyebab allocator/driver belum dipastikan meskipun log melaporkan memori bebas lebih besar. Kedua model ditetapkan memakai `kv_cache_memory_bytes=6442450944` (6 GiB), cukup untuk KV BF16 satu sequence 32K yang terhitung 4 GiB. Ini menggantikan kalkulasi cache dari `gpu_memory_utilization=0.80`; flag 0,80 bukan lagi ukuran cache efektif. Konteks, bobot, dtype, sampling, prompt, parser, input, dan stop tokens tidak berubah. Protokol awal beserta 27 sumber dan log kegagalan diarsipkan di `startup-initial/`, lineage/hash dicatat di `cache-amendment.json`, kemudian 30 checksum sumber dibekukan ulang sebelum request pertama. Perbedaan cache dengan kontrol historis membatasi interpretasi latency.
- **Penyelesaian 1 Oktober 2026, 09:24 WIB:** 3.892 respons baru unik selesai, 1.946 request generasi HTTP 200 per model, tanpa retry request/error transport; kedua server berhenti normal. 30 checksum sumber aktif, 13 kontrol, dan 27 sumber arsip awal cocok. Phi DIFF/DIFF+I: recall sumber 45,93%/50,29%, FPR TYP 13%/13%, JSON valid 58,17%/82,94%. Llama DIFF/DIFF+I: recall 85,45%/89,23%, FPR 57%/69%, JSON valid 88,08%/89,62%. Invalid baru 790, termasuk 219 terpotong. Tidak ada perubahan protokol setelah prediksi pertama; amendemen cache tetap terdokumentasi. Tabel 12 kombinasi dari enam model dan dua konfigurasi berisi 11.676 respons, termasuk kontrol D82/D83, di `docs/model-families-20261001.md`. Hasil tidak menunjukkan satu model baru unggul menyeluruh; kenaikan Llama DIFF+I terhadap Qwen2.5-7B DIFF+I terutama melalui transisi valid/invalid. Tidak ada pemilihan prompt berdasarkan hasil, klaim konfirmatori, atau penambahan model berikutnya secara otomatis.


**D85. Pengembangan format dan verifikasi bukti dipisahkan dari evaluasi akurasi.**

- Pengguna menyetujui kelanjutan diagnosis FPR. Dibuat indeks ID baris yang membedakan added/deleted/context dan memeriksa keberadaan kutipan tanpa mengubah verdict. Tidak menganggap ID valid sebagai bukti kebenaran semantik.
- Eksperimen dev nyata Qwen3-4B memakai 32 kandidat HN belum dievaluasi, dipilih deterministik berdasarkan hash sebelum prediksi; untruncated <=16.000 token, nama/hash diff/arsip berbeda dari kontrol historis. Kelimanya: LEGACY-I, SCHEMA-I, IDS-I, IDS-D, VERIFY-I; 160 generasi. Detail dan seluruh batas interpretasi ada di docs/evidence-dev-20261001.md.
- LEGACY-I/SCHEMA-I memakai pesan sama, hanya kendala decoder berbeda. IDS-I mengganti representasi/format; IDS-D menghapus intent. Verifier memeriksa ulang semua kandidat IDS-I, bukan hanya alarm. Panggilan tambahan dan biayanya dilaporkan.
- Semua label masih pending; yang diukur validitas, keterlacakan kutipan, transisi, token/latency, bukan recall/FPR. Paket dev dan klon terkait dikeluarkan dari test/KB final. HN belum memiliki pemetaan kampanye, sehingga pemisahan nama/hash tidak dianggap independensi kampanye. Tidak membuat label/card palsu, mengubah hasil historis, atau menyetel pada test. Gold/HN/MB dan G1/G2 belum selesai.
- BF16, seed 0, temperature 0, top_p 1, output 2.048, konteks 32.768, KV 6 GiB, satu sequence. Sumber dan input dibekukan sebelum inferensi, token aktual diverifikasi, invalid dipertahankan, error transport menghentikan batch tanpa retry otomatis.

**D86. Dev campuran disiapkan untuk anotasi independen sebelum menilai trade-off alarm dan recall.**

- Kelanjutan yang disetujui pengguna menambahkan 32 kandidat MAL dari 32 kampanye berbeda ke seluruh 32 kandidat HN D85. MAL dipilih tanpa membaca prediksi: urut SHA-256 `D86|campaign`, lalu `D86|id`, maksimal satu per kampanye/nama/hash diff/arsip, tidak terpotong dan <=16.000 token diff sebelumnya. Semua calon MAL telah terpapar eksperimen D81–D84 dan HN terpapar D85; ini dev eksploratif, bukan holdout baru. Pemetaan kampanye HN belum tersedia.
- Paket anotasi memakai ID netral, urutan hash, dan proyeksi field yang menyembunyikan subset sumber, kampanye, kategori sinyal, label, dan prediksi. Identitas paket, intent, capability delta otomatis, dan diff tetap terlihat; tidak diklaim buta terhadap seluruh reputasi paket. Kedua anotator harus manusia berbeda dan menilai secara independen. Kolom bukti dan kategori tersedia untuk semua sampel.
- Skrip kesiapan hanya memeriksa kelengkapan, bukti verbatim pada konten perubahan, serta kesepakatan label/kategori. Kecocokan teks atau dua nama akun tidak membuktikan kebenaran semantik maupun dua manusia. Tidak mengekspor gold otomatis. Kesepakatan, bukti, tujuan sah, dan identitas diperiksa manusia sebelum konsensus. Sampel `skip`/tidak sepakat dicatat sebagai attrition; tidak diganti berdasarkan hasil agar kuota tampak terpenuhi.
- Tahap ini tidak membuat inferensi, metrik recall/FPR, atau label baru. Audit konteks semua prompt dan pembekuan protokol inferensi berikutnya masih diperlukan. Seluruh sampel dev, nama/hash/klon terkait, dan kampanye MAL terpilih dikecualikan dari test/KB final. Seleksi final harus menerapkan berkas pengecualian ini; G1/G2 tetap belum selesai.
- Artefak ada di `data/evaluation/mixed-dev-20261002/`. Sebelum append ini, `docs/decisions.md` disalin ke `decisions-through-D85.md` di direktori tersebut dan hash dicocokkan dengan pin D85. Manifest/protokol/hasil D85 tidak diubah; hash dokumen historis tetap merujuk versi sebelum D86, bukan dokumen hidup setelah append.


**D87. Validasi intervensi D85 diperluas ke MAL dengan label sumber secara eksploratif.**

- Pengguna mengoreksi arah agar kembali ke penelitian dan menyetujui kelanjutan dev campuran. Batas gold tetap berlaku untuk klaim, bukan menghentikan seluruh eksperimen eksploratif yang telah diizinkan D81.
- Semua 32 MAL dari seleksi D86 dipakai pada lima arm D85, menghasilkan 160 inferensi baru. Hasil 32 HN D85 (160 respons) menjadi kontrol historis tanpa dijalankan ulang. Prompt/model/parser/parameter tetap; tanpa perubahan intervensi berdasarkan hasil MAL.
- MAL dilaporkan sebagai recall proxy label sumber; HN hanya jumlah alarm, bukan FPR. Laporkan invalid, transisi, bukti, serta biaya. Tidak ada klaim gold, manfaat RAG, atau uji hipotesis utama. Pembatasan anotasi D86 tetap berlaku untuk gold; tahap baru ini secara eksplisit memakai label sementara.
- Detail dibekukan di `docs/mixed-validation-20261011.md`; artefak di `data/evaluation/mixed-validation-20261011/`. Dokumen keputusan sebelum entri ini diarsipkan sebagai `decisions-through-D86.md`, menjaga jejak pin D86. Snapshot dan hasil D85 tidak diubah.


**D88. Diagnosis dependency dilakukan sebagai evaluasi versi bersyarat, dengan perlindungan kebocoran KB.**

- Setelah kelanjutan disetujui pengguna, seluruh 20 target D87 yang menambahkan easy-day-js diuji dengan konteks sumber versi 1.11.21 dan 1.11.22: 40 inferensi nyata baru. Ini subgroup post-hoc dari dev terpapar, bukan holdout. Kedua versi cocok rentang dan terbit sebelum target menurut metadata arsip; tanpa lockfile, versi instalasi aktual tidak diketahui. Tidak menetapkan gold benign/malicious bagi snapshot dependency.
- Prompt IDS-I dan model/parameter D87 dipertahankan, dengan instruksi kondisional identik untuk kedua arm serta berkas manifest/main/install-hook tanpa label keamanan. Semua sumber dipin sebelum inferensi; raw respons, token, transisi, validitas dan kutipan dilaporkan. Tidak mengeksekusi sampel atau mengakses endpoint sampel. Detail: docs/dependency-context-20261011.md.
- Dua puluh target berbagi satu keluarga dependency. Tidak mengklaim 20 insiden independen, FPR, recall instalasi aktual, manfaat RAG, atau keberhasilan hipotesis utama. Kontrol IDS-I D87 historis tidak dijalankan ulang; tambahan instruksi membatasi perbandingan terhadap kontrol itu.
- Filter KB lama meloloskan 40 kombinasi target–versi dependency karena nama/cluster berbeda. Filter mendatang juga menolak identitas dependency yang berubah dan pengecualian nama eksplisit. Konteks dependency tanpa label dipisahkan dari contoh KB berlabel. Belum ada card nyata terverifikasi untuk MM/MB; tidak menggunakan fixture sebagai hasil. Snapshot historis tidak diubah; keputusan sebelumnya diarsipkan dalam decisions-through-D87.md.

- **Penyelesaian 12 Oktober 2026, 00:31 UTC+7:** 40 inferensi baru selesai, semuanya HTTP 200/JSON valid, tanpa length truncation atau unknown ID. Konteks 1.11.21 menghasilkan 20 benign dan 1.11.22 menghasilkan 20 malicious. Seluruh request/token/parser/citation serta 21 sumber, tiga kontrol, 13 model pin cocok; server berhenti. Hanya 14/20 respons positif mengutip isi setup.cjs. Total 370.164 token. Hasil merupakan diagnosis versi bersyarat pada satu keluarga dependency, bukan recall 100%, FPR, atau manfaat RAG. Laporan: docs/dependency-context-results-20261012.md.


**D89. Isi dependency diuji dengan instruksi kondisional sejajar pada kohort yang tersedia.**

- Kelanjutan pengguna memperluas diagnosis D88. Seleksi memakai dependency tercatat, kecocokan semver, ketersediaan arsip, tanggal rilis, keterbacaan file dan batas konteks; bukan prediksi. Seluruh target easy-day-js dikeluarkan. Audit awal menemukan hanya satu target MAL di luar keluarga itu; tidak mengklaim generalisasi lintas keluarga serangan.
- Maksimal satu pair per nama dependency/target berdasarkan hash D89, tanpa kuota label hasil. Versi lokal terbaru yang cocok dan mendahului target dipilih; versi terpasang tetap tidak terverifikasi. Dua kondisi baru NO-SOURCE/WITH-SOURCE memakai instruksi asumsi identik dan hanya berbeda ketersediaan isi berkas. Snapshot model/parameter D88 dipertahankan; semua request dibekukan sebelum inferensi.
- HN dilaporkan sebagai alarm, bukan FPR. MAL terbatas tidak menjadi estimasi recall populasi. Paparan dev dan pengecualian KB/test dicatat, tanpa gold/card buatan, eksekusi sampel atau perubahan hasil historis. Protokol: docs/dependency-generalization-20261012.md. Arsip: data/evaluation/dependency-generalization-20261012/.

- **Penyelesaian 12 Oktober 2026, 01:09 UTC+7:** 15 target (14 HN pending, satu MAL sumber) × dua arm menghasilkan 30 respons HTTP 200/JSON valid tanpa unknown ID/length truncation. Semua verdict benign di kedua arm; tidak ada perubahan atau kenaikan deteksi. 44 kandidat target–versi gugur karena dependency terbit sesudah target. Semua HN terpilih hanya memiliki delta dependency_change dan semua snapshot tanpa install hook, sehingga tidak mewakili HN runtime sensitif. Total 196.035 token, WITH-SOURCE 1,89× NO-SOURCE. 91 sumber, 21 input/provenance dan 13 model pin cocok; server berhenti. Tidak ada klaim FPR 0%, gold, atau RAG. Laporan: docs/dependency-generalization-results-20261012.md.


**D90. Model baru Granite 3.3 8B diuji pada seluruh kondisi D89 tanpa mengubah data/prompt.**

- Pengguna secara eksplisit meminta model baru. Granite revisi 51dd4bc2ade4059a6bd87649d68aa11e4fb2529b dipilih sebelum keluaran model, bukan berdasarkan kenaikan pada cohort. Model ini baru untuk inferensi penelitian; kandidat/metadata telah diaudit D84. Bobot resmi diunduh dan hash diperiksa, tanpa remote-code.
- Seluruh 15 target × dua arm D89 dipertahankan: 30 inferensi baru. Qwen3-4B D89 menjadi kontrol historis. Pesan/schema/parser, urutan dan parameter bersama sama; native template Granite thinking=false dan EOS [0] dicatat eksplisit. Preflight maksimum 24.467 token muat pada 32.768 dengan output 2.048; KV 6 GiB, BF16, greedy, seed 0.
- Semua hasil dilaporkan, tidak menjamin model baru lebih baik. Satu MAL dan HN pending tidak menghasilkan klaim akurasi gold/FPR atau efek kausal ukuran. Tidak ada perubahan hipotesis RAG utama, penambahan fixture, atau pencampuran ke data/results.jsonl. Protokol: docs/granite-dependency-20261012.md.
