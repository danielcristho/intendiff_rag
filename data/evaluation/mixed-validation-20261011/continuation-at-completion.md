# Posisi kelanjutan — 11 Oktober 2026

Pengguna meminta fokus eksperimen penelitian dan validitas, bukan frontend/backend.
Tujuan utama tetap benign contrastive retrieval: DIFF+I+MB vs DIFF+I+MM;
ablation intent DIFF+I+MB vs DIFF+MB. Model lebih besar dan decoder merupakan
analisis pendukung, bukan pengganti RQ. D81 mengizinkan eksplorasi label sumber;
jangan mengarang gold atau menganggap ketiadaan gold menghentikan semua analisis.

D87 selesai: baca docs/mixed-validation-results-20261011.md.
160 inferensi baru Qwen3-4B pada semua 32 MAL D86, lima kondisi D85 identik;
160 HN D85 dipakai sebagai kontrol historis. Semua request/hash/token/parser
terverifikasi; server sudah berhenti. Jangan menggandakan batch.

MAL positif LEGACY-I 18, SCHEMA-I 19, IDS-I 11, IDS-D 11, VERIFY-I 10 dari 32.
HN historis alarm 5/6/0/0/0, bukan FPR gold. Seluruh delapan deteksi hilang
schema→ID berada pada subgroup 20 pair dengan penambahan easy-day-js; ID menilai
semua 20 benign. Subgroup 12 lain tetap 11 deteksi sebelum verifier, kemudian 10.
Analisis subgroup post-hoc; bukan sebab kausal atau label otomatis.
32 ID klaster tidak membuktikan 32 insiden independen; shared dependency perlu audit.

Kesimpulan: intervensi ID/verifier belum menjadi perbaikan; jaga hasil negatif.
Kelanjutan kembali ke kecukupan konteks dependency, clustering insiden, dan
card pembanding MB/MM terverifikasi. Tidak ada retrieval dijalankan di D87.
Jangan menyetel ulang D87, membuat blacklist nama, atau mengklaim recall/FPR gold.
Gold, pemisahan KB/test, dan G1/G2 tetap belum selesai. Kandidat D86 tetap dev.
