# Posisi kelanjutan — 12 Oktober 2026

**TUGAS AKTIF D92: pengguna meminta rerun nyata seluruh model dengan perubahan
kode; jangan kembali hanya menjelaskan tabel historis atau membuat pilot.**
Persiapan data/evaluation/full-method-20261012/: 973 pair asli ×7 model ×
IDS-D/IDS-I/VERIFY-I =20433 inferensi baru. Prompt/evidence D87 byte-identik.
Konteks dependency bersyarat terpisah; tidak tersedia lengkap untuk973pair.
Audit sebelum run memotong prefix diff sekali per pair jika diperlukan agar
semua tokenizer muat; semua973pair dipertahankan. Lihat docs/full-method-20261012.md.
Periksa status.json/progress.json serta proses yang berjalan sebelum bertindak;
jangan menjalankan controller kedua atau mengubah sumber setelah protocol.json
dibekukan. Hasil baru harus selesai diverifikasi seluruh model sebelum tabel
lengkap paper; jangan campurkan respons D82–D90. Gold/RAG belum selesai.

**Instruksi pengguna terbaru (D91): seluruh eksperimen yang diklaim di paper
harus benar-benar dijalankan lengkap sesuai matriks yang ditetapkan.** Jangan
menggantikan evaluasi penuh dengan subset, fixture, simulasi, atau proyeksi.
Bekukan cakupan sebelum inferensi; periksa kombinasi yang diharapkan terhadap
respons mentah unik. Catat invalid/kegagalan/kekurangan dan kontrol historis
secara terbuka. Label gold/card KB tetap harus sah; jangan membuatnya sendiri.
D82–D84 telah diaudit: 11676 respons unik, 6 model × 2 arm × 973 pair identik.
D88 (20 target) serta D89/D90 (15 target) hanya diagnosis subset, belum evaluasi
penuh dependency/Granite. RAG utama belum selesai. Prioritaskan menyelesaikan
cakupan eksperimen yang disepakati, bukan terus membuat pilot kecil sebagai
pengganti. Tidak ada inferensi baru pada turn penegasan ini.

**Terbaru: D90 selesai 05:44 UTC+7; jangan ulangi inferensi.**
Pengguna meminta model baru lalu penulisan hasil ke LaTeX. Granite 3.3 8B
Instruct revisi 51dd4bc2ade4059a6bd87649d68aa11e4fb2529b menjalankan seluruh
15 target × dua arm D89 = 30 respons baru; dibandingkan 30 Qwen historis.
Semua benign pada kedua model/arm: 14 HN pending dan satu MAL sumber.
Tidak ada kenaikan deteksi; bukan FPR 0% atau kesetaraan model secara umum.
Semua valid, nol length/unknown ID/transport error. Total Granite 223382 token;
dua WITH-SOURCE mengutip isi dependency. 27 source +6 upstream +14 model pin
cocok; payload/token/parser/kutipan diperiksa ulang; server berhenti normal.
Tiga test lulus. Laporan docs/granite-dependency-results-20261012.md,
artefak data/evaluation/granite-dependency-20261012/. Bobot lengkap tersedia
lokal data/upstream/models/granite33_8b. Jangan mengubah snapshot beku.

Hasil D88–D90 ditulis dalam labs/latex/results-exploratory.tex dan
discussion-exploratory.tex, di-input naskah intendiff-rag.tex. Penulisan
eksploratori diperbolehkan; gold/card A/B/split dan hasil MM vs MB masih belum
selesai. Jangan mengisi abstrak/kesimpulan utama seolah hipotesis terbukti.
Prioritas berikut tetap sumber dependency relevan, HN runtime sah, versi dan
provenance, anotasi dan card A/B; menambah model saja belum memperbaiki hasil.
PDF labs/latex/intendiff-rag.pdf berhasil dibangun 13 halaman; build guide
labs/latex/BUILD.md. Sitasi/referensi terdefinisi, warning tata letak bagian
lama masih ada. Tree dependency LaTeX sementara di /tmp/intendiff-texmf.

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


D89 SELESAI, kelanjutan terbaru: docs/dependency-generalization-results-20261012.md.
Jangan ulangi D88/D89 atau mengedit snapshot beku. Direktori D89:
data/evaluation/dependency-generalization-20261012/. 30 inferensi baru pada
15 target (14 HN pending + satu MAL sumber zuper-cli@1.0.1), dua arm NO-SOURCE
vs WITH-SOURCE dengan instruksi kondisional identik. Semuanya benign di kedua
arm: tidak ada perubahan, belum ada perbaikan deteksi/FPR. Semua valid, nol
length/unknown ID/error transport. 91 sumber +21 input/provenance +13 model pin
cocok, lima test lulus, server berhenti. Total 196035 token; WITH-SOURCE 1.89×.

Audit seleksi: 67 kombinasi semver lokal; 44 future versions dikeluarkan,
2 self-dependency,1 versi lebih lama,5 shared-name cap;15 dipilih berdasarkanhash.
Semua target easy-day-js dikeluarkan,15 nama dependency,versi terbaru lokal yang
cocok dan mendahului target. 64 metadata timestamp registry berhasil diambil
(tanpa mengunduh/menjalankan kode baru). Versi terpasang tetap belum diketahui.
Enam target pernah masuk D86. Semua 14 HN hanya delta dependency_change; nol
snapshot memiliki install hook. Jangan klaim telah menguji HN runtime sensitif,
15 keluarga serangan, atau FPR 0%. Hanya2 WITH-SOURCE mengutip isi dependency.

Kelanjutan konkret: lengkapi sumber dependency relevan dan HN runtime sah,
bukan mengulang cohort mudah atau menambah model secara otomatis. Baca
missing-dependency-sources.json D89: @antv/setup 4 target MAL untruncated,
@opensearch/setup 2; itu daftar ketersediaan, bukan label malicious dependency.
Perlu provenance/tanggal/semver/coverage sebelum konteks dipakai. D89dev-exclusions
adalah sidecar yang harus diterapkan seleksi KB/test; loader belum otomatis.
Tujuan utama tetap MM vs MB dan intent ablation dengan card A/B terverifikasi.
