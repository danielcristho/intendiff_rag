# Posisi kelanjutan — 12 Oktober 2026

Pengguna meminta fokus eksperimen dan validitas, bukan UI/backend.
Tujuan utama tetap DIFF+I+MB vs DIFF+I+MM; ablation DIFF+I+MB vs DIFF+MB.
D81 mengizinkan eksplorasi label sumber, bukan gold buatan atau FPR HN pending.

D87 selesai: docs/mixed-validation-results-20261011.md. Seluruh 32 MAL D86 ×
lima arm = 160 inferensi baru; HN historis D85 160 respons. Positif MAL
LEGACY-I/SCHEMA-I/IDS-I/IDS-D/VERIFY-I = 18/19/11/11/10. HN alarm 5/6/0/0/0,
bukan FPR. Seluruh delapan deteksi schema→ID yang hilang berada pada 20 target
penambahan easy-day-js; 20 target berbagi dependency meski cluster ID berbeda.

D88 SELESAI: docs/dependency-context-results-20261012.md.
40 inferensi nyata Qwen3-4B (20 target × dua snapshot dependency), tanpa label
keamanan dalam konteks. Konteks 1.11.21: 20 benign; 1.11.22: 20 malicious.
Keduanya cocok rentang ^1.11.21 dan mendahului target menurut metadata arsip,
tetapi tidak ada lockfile yang menetapkan versi instalasi aktual. Ini hasil
bersyarat, bukan recall 100%, bukan solusi FPR, bukan pengujian RAG.
Direktori tetap data/evaluation/dependency-context-20261011 (tanggal persiapan).

Semua 40 valid, nol length/unknown ID, request/token/parser/citation/hash cocok.
21 sumber + 3 kontrol + 13 model pin cocok. Server sudah berhenti; jangan ulangi
batch. Total 370164 token. 18/20 respons 1.11.22 mengutip konteks, tetapi hanya
14/20 mengutip isi setup.cjs; reasoning tambahan belum terverifikasi semantik.
Tidak mengeksekusi kode sampel atau menghubungi endpoint-nya.

Filter KB live pipeline/runner.py kini juga menolak nama pada
 delta_evidence.dependency_change dan retrieval_exclude_names. Audit: old eligible
40, new eligible 0 pada target × versi dependency. Empat test_dependency_context
lulus dan runner selfcheck lulus. Bukti extractor terbatas: bukan seluruh perubahan
versi/transitive/alias. Sidecar retrieval-exclusions.jsonl 64 pair tersedia tetapi
belum otomatis digabung loader. 20 target terlindungi dari metadata asli.
Snapshot D85/D87/D88 dibekukan; jangan mengeditnya setelah hasil.

Kelanjutan: kohort dependency multi-insiden + HN sah, audit versi resolved vs
ambigu, kontrol instruksi sejajar; kemudian MM/MB dengan card A/B terverifikasi.
Belum ada card nyata terverifikasi: jangan membuat label manusia atau memakai
fixture sebagai hasil. Gold, split KB/test, dan G1/G2 tetap belum selesai.
Semua target terpapar ini dev; jangan pindahkan ke test final atau campurkan
hasil kondisional D88 ke recall D87. Pertahankan hasil negatif dan batas klaim.
