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

**D58. Sampel TYP tidak ada di paket replikasi; kerangka sampelnya masih hidup di registry npm.**

- Isi zip diperiksa per baris terhadap direktori yang benar-benar terekstrak:

| Daftar | Baris | Ada isinya |
|---|---|---|
| `malicious_updates.txt` (MAL) | 46 | **46 direktori, 45 berisi** (D59) |
| `malicious_clones.txt` | 171 | **171** |
| `typical_updates_popular.txt` | 1.000 | **0** |
| `typical_updates_random.txt` | 1.000 | **0** |

- `code/automated_b_samples/` dan `code/r_samples/` adalah **direktori kosong** (0 byte) di dalam zip. Yang dirilis hanya daftar `paket@versi`, bukan tarball-nya. MAL dan clone lengkap, sehingga §3.1 dan KB malicious bisa dibangun offline.
- Ketersediaan 2.000 typical update dicek ke `registry.npmjs.org` pada 2026-09-19, kedua versi per pair:

| | Lengkap | Paket 404 | Kedua versi hilang |
|---|---|---|---|
| Popular | **1.000** | 0 | 0 |
| Random | **981** | 10 | 9 |

- **1.981 dari 2.000 pair masih bisa dibangun.** Yang hilang seluruhnya dari kelompok acak, dan contohnya paket sangat kecil (`qietuzai-cli`), konsisten dengan unpublish biasa.
- **Dampak:** §3.2 mengambil 100 TYP dan §3.3 jalur A memakai 1.900 sisanya, jadi kehilangan 19 (0,95%) tidak mengancam keduanya. Aturan pengganti di §3.2 sudah menangani pair yang gugur. Tarball ditarik lewat `collect.py`, bukan dari OSF.
- `malicious_packages.zip` dan `malicious_updates.zip` punya CRC identik (`277aa32c`) — satu file diduplikasi, bukan dua korpus.

**D59. MAL terpakai 45 pair, bukan 46, dan direktori versi harus dibaca menembus pembungkus `package/`** (§3.1).

- **Pembungkus tarball.** 60 dari 92 direktori versi di paket replikasi masih memuat direktori `package/` bawaan tarball npm; 31 sisanya rata. Dibaca apa adanya, `package.json` jadi tak terlihat, sehingga profil intent kosong dan seluruh sinyal yang diturunkan dari manifest (`install_script`, `dependency_change`) tidak pernah menyala. Terdeteksi dari angka **31 dari 46 pair tanpa intent**; setelah pembungkusnya dibaca, tinggal **1**.
- Tidak ada pair yang pembungkusnya berbeda antara v_(t−1) dan v_t, jadi smart-diff sebelumnya tidak rusak — hanya membawa prefix `package/` di setiap path.
- **`stream-combine@2.0.2` dikeluarkan.** Direktori v_(t−1) (`stream-combine@2.0.1`) ada tetapi **kosong**. Men-diff-kan v_t terhadap direktori kosong menyajikan seluruh paket sebagai file baru, dan itu bukan update.
- Verifikasi D58 sebelumnya hanya mengecek direktorinya ada, bukan berisi; angka "46/46" di sana dikoreksi.

Hasil `data/pairs.mal.jsonl`: **45 pair, 41 kampanye, 1 terpotong, 1 tanpa intent, 42 punya capability delta tidak kosong.**

| Sinyal | Pair |
|---|---|
| `network` | 30 |
| `browser_data` | 28 |
| `obfuscation` | 9 |
| `install_script` | 8 |
| `process_exec` | 5 |
| `dependency_change` | 3 |

- `browser_data` menyala di 28 dari 45 (62%), sejalan dengan klaim Wyss bahwa 33 dari 46 insiden asli adalah form grabbing.
- Dua kampanye memuat lebih dari satu pair: `rc-calendar-jhorst@8.4.3` (4) dan `coa@2.0.3` (2). Sisanya tunggal, karena kriteria (a) advisory belum terisi dan (c) Dolos belum bisa dijalankan (D56).
- **`sha256_before`/`sha256_after` memuat digest pohon, bukan digest tarball**, karena yang dirilis adalah direktori terekstrak. Dihitung dari daftar terurut `path\0sha256`, jadi tetap stabil di mana pun diekstrak.
- **`gold_evidence` sengaja kosong.** Baris bukti gold berasal dari anotasi §8, tidak boleh diturunkan dari extractor — kalau tidak, metrik lokalisasi bukti hanya mengukur extractor terhadap dirinya sendiri.

**D60. TYP terkumpul: 100 pair, diundi dari daftar Wyss dan ditarik dari registry npm** (§3.2).

- 50 dari `typical_updates_popular.txt` dan 50 dari `typical_updates_random.txt`, diambil menurut urutan SHA-256 `name@version`, bukan popularitas.
- **Lima undian ditolak karena punya advisory** dan diganti undian berikutnya, sesuai §3.2: `@babel/core@8.0.0-alpha.8`, `@babel/runtime@8.0.0-alpha.8`, `@angular/common@18.0.0-next.4`, `http-cache-semantics@4.1.1`, `jws@4.0.0`. Semuanya dari kelompok populer, yang memang wajar — paket populer lebih sering punya CVE tercatat.
- Tarball diekstrak dengan `tarfile.extractall(..., filter="data")`, yang menolak path absolut, symlink, dan `..`. Paket tidak pernah di-`npm install` maupun dijalankan.

| | MAL (45) | TYP (100) |
|---|---|---|
| Capability delta kosong | 3 (7%) | **86 (86%)** |
| Terpotong (§4.5) | 1 (2%) | 15 (15%) |
| Panjang diff, median | 6.941 char | 1.277 char |
| Panjang diff, p95 | 30.317 char | **103.405 char** |
| Sinyal terbanyak | `network` 30, `browser_data` 28 | `dependency_change` 13 |

- **Pemisahan capability delta bekerja seperti yang diharapkan §4.3.** MAL menyala di 42 dari 45; TYP diam di 86 dari 100, dan yang menyala hampir semuanya `dependency_change` — perubahan rutin, bukan payload.
- **Dampak pada retrieval:** untuk 86 pair TYP, skor Jaccard terhadap setiap card adalah 0, sehingga card yang terpilih ditentukan tie-break SHA-256 §5.2 langkah 3. Aturannya sudah ada dan deterministik, jadi tidak ada celah desain — tetapi artinya E2, E3, dan E4 pada sebagian besar TYP mengukur "apakah card yang tidak relevan merusak", bukan "apakah card yang relevan menolong". Itu justru yang relevan untuk FPR_TYP, dan harus disebut saat membaca hasilnya.
- **TYP lebih panjang daripada MAL di ekor atas:** p95 103.405 char melawan 30.317. Update rutin bisa menyentuh seluruh pohon, sementara payload malicious biasanya kecil dan terpusat. Karena itu pemotongan §4.5 mengenai TYP tujuh kali lebih sering daripada MAL.

## 2026-09-26 — Card malicious KB dan dev set

**D61. 50 card malicious dipilih dari Datadog; teksnya ditulis anotator, bukan oleh model** (§3.4, §5.1).

- Dataset Datadog diambil sebagai clone *blobless* (commit `a9749c04`), dan isi sampel ditarik hanya untuk kandidat yang diperiksa. Pool: **21.068** sampel npm `malicious_intent` yang manifest-nya `null`. Sampel diekstrak dengan `ZipFile.extractall` (tanpa symlink, tanpa `..`), dibatasi 50 MiB, dan hanya dibaca.
- Round-robin atas 8 capability dalam urutan tabel §4.3, menurut urutan hash. Cukup **358 sampel** dipindai untuk mengisi 50 card: 7 card per capability untuk `network` dan `process_exec`, 6 untuk sisanya.
- **44 kampanye**, 6 di antaranya berisi 2 card. 12 sampel dilewati karena kampanyenya sudah penuh, 2 karena tidak terbaca, dan **0** karena kampanyenya ada di MAL.
- **Angka 0 itu belum bukti tidak ada kebocoran.** 45 pair MAL hanya menghasilkan **17** digest file tambahan, karena sebagian besar payload MAL disisipkan ke file yang sudah ada. Kriteria (b) §3.6 jadi lemah sebagai penjaga KB–test, dan kriteria (c) Dolos belum bisa dijalankan (D56). Sampai Dolos jalan, pengecualian per kampanye praktis hanya bersandar pada nama paket.
- **Root paket:** sampel Datadog dibungkus `tmp/<acak>/<nama>/` bersama `package_info-*.json` milik Datadog. Root diambil dari `package.json` terdangkal di luar `node_modules`, jadi file metadata itu tidak ikut dipindai atau di-hash.
- **Field `name` ditambahkan ke skema card.** `runner.eligible` sudah mengecualikan card lewat `name`, tetapi skema di experiments.md belum mencantumkannya.
- **Teks card (`intent`, `behavior_chain`, `code_excerpt`, `rationale`) ditulis anotator A lalu dicek anotator B, sesuai §5.1.** Opsi agar Claude menyusun draf ditolak, karena draf itu termasuk output model. `data/kb.skeleton.jsonl` membawa `delta_evidence` dan `selected_for` sebagai penunjuk ke kode. Kedua field itu dibuang saat card dipromosikan ke `data/kb.jsonl`.

**D62. Dev set: 4 clone Wyss dan 3 TYP yang belum terpakai; 3 HN menyusul** (§3.5).

- **Clone** diambil menurut urutan hash dari `nama_asli@direktori_clone`. `malicious_clones.txt` tidak memberi versi di sisi clone (`j_samples/agent-base/agentbas-7.1.1`), jadi nama direktori clone yang dipakai sebagai identitas. Ke-171 clone berisi.
- **TYP** diundi menurut urutan hash dari gabungan kedua daftar Wyss, setelah membuang 100 pair TYP test, dengan aturan advisory §3.2 (empat undian ditolak, sama dengan D60). Hasilnya: `ant-mini-flip-draw@1.0.2`, `react-d3-library@1.1.8`, `snappydown@0.0.2`.
- **Ketiga TYP dev dicatat di `data/pairs.dev.taken.txt` dan harus dikecualikan dari jalur A** (§3.3). Tanpa itu, pair yang dipakai untuk memverifikasi mekanisme bisa muncul lagi sebagai item uji HN.
- Isinya mencakup kasus yang perlu dilalui mekanisme pipeline: 3 dari 7 pair terpotong, 3 TYP dengan delta kosong, dan 2 clone dengan `large_deletion`.
- **Replikasi di server:** `pairs.mal.jsonl` yang dibangun ulang dari zip OSF (sha256 cocok dengan D56) identik byte-per-byte dengan versi di git.

**D63. Card ditulis dan dicek lewat UI dalam empat tahap; `kb.jsonl` hanya ditulis kalau semua card disetujui** (§5.1).

- Tahap: **kosong → draf → menunggu cek → disetujui**. Card yang dikembalikan pengecek kembali ke draf dengan alasan wajib. Card yang sudah disetujui terkunci sampai pengecek membukanya lagi.
- **Penulis ≠ pengecek dipaksa di backend** (`backend/src/cards.rs`), bukan hanya disembunyikan di UI. Penulis card ditentukan per card oleh siapa yang pertama menulisnya.
- Teks card disimpan di `data/kb.cards.json`, satu file bersama. Beda dengan keputusan audit (§8), card memang dikerjakan berdua, jadi tidak ada independensi yang perlu dijaga.
- **`code_excerpt` dipilih dari rentang baris sampel di UI**, bukan diketik, supaya verbatim. `pipeline/promote.py` memeriksanya lagi: setiap baris excerpt harus ada di file sampel.
- **Batas token dicek saat promosi dengan tokenizer Qwen**: intent ≤ 64 token, card ≤ 512 token yang dihitung atas blok yang benar-benar dilihat model (`prompts.examples_block`). Card yang melebihi batas **ditolak, tidak dipangkas otomatis**. Memangkas excerpt verbatim tanpa anotator berarti mengubah card yang sudah dicek.
- **Promosi menolak menulis `kb.jsonl` parsial.** Runner otomatis beralih ke `kb.sample.jsonl` kalau `kb.jsonl` tidak ada, dan akan memakai KB parsial tanpa peringatan.
- **Promosi tetap lewat CLI, tidak lewat tombol di UI.** Backend terbuka di jaringan host GPU tanpa autentikasi, dan menjalankan skrip dari endpoint HTTP menambah permukaan serangan.

## 2026-09-26 — Smoke test dev set pertama dengan model sungguhan

**D64. Smoke test E0/E0-noint atas 7 pair dev set: validitas JSON 10/14; prefix caching vLLM mencemari latensi** (§6.4, §9.2).

- Server: vLLM **0.29.0**, `Qwen/Qwen2.5-Coder-3B-Instruct`, bf16, `--max-model-len 32768`, `--seed 0`, tanpa kuantisasi, `--gpu-memory-utilization 0.80`, RTX 5080 16 GB. Hasil di `data/results.dev.jsonl`, terpisah dari test.
- **Warm-up §9.2 ternyata belum ada di runner.** Sekarang runner mengirim 3 request E0 dari `data/pairs.dev.jsonl` sebelum run pertama, tanpa dicatat.
- **Validitas JSON 10/14 (71%)**: E0 5/7, E0-noint 5/7. Angka ini di bawah ambang 90% §6.4, tetapi dev set baru 7 dari 10 pair, jadi keputusan revisi format **belum** diambil.

| Penyebab tidak valid | Run |
|---|---|
| `finish_reason=length` (512 token): `evidence` diisi seluruh hunk diff, bukan ≤ 3 baris | 2 |
| JSON rusak: `"` tidak di-escape di dalam string | 1 |
| JSON rusak: karakter tab mentah di dalam string | 1 |

- Semua jawaban dibungkus pagar kode ` ```json `. Parser tetap membacanya karena mencari `{` pertama.
- Pair dengan prompt 28–29K token (smart-diff terpotong §4.5) diproses tanpa error dan muat di konteks 32K.
- **Prefix caching aktif** (`enable_prefix_caching=True`, default vLLM 0.29, hit rate 22–33%). Warm-up mengirim prompt yang sama dengan run terukur pertama, sehingga run itu tercatat 1,2 s, sedangkan E0-noint pada pair yang sama 4,0 s. Methodology tidak mengatur prefix caching, jadi latensi RQ4 saat ini bergantung pada urutan run. **Keputusan terbuka**, harus diambil sebelum G2.
- Verdict dev set tidak ditafsirkan (§3.5).
