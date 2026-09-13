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

**D22. Posisi penelitian: triage update dependensi sebelum advisory terbit (pelengkap `npm audit`), bukan audit tata kelola TI.**
- Alasan: menyamakan ekspektasi pembaca dan penguji.
