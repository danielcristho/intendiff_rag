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


## D94–D95: akuisisi dataset diperluas selesai, 13 Oktober 2026

Pengguna menyetujui penguatan dataset untuk Q1. Laporan terbaru:
docs/dataset-expansion-results-20261013.md; panduan anotasi:
docs/dataset-expansion-review-20261013.md. Completion dan manifest 175 berkas:
data/acquisition/expansion-full-20261013/completion.json serta artifact-manifest.json.

TYP 2.257 kandidat (902 popular, 974 random, 381 stream dengan nama belum dipakai).
HN 383 kandidat mentah (182 lama + 201 baru); 325 lolos prefilter (162+163).
Overlap TYP/HN lolos=162, sehingga review berisi 2.420 ID unik. Dari HN baru
yang lolos, 91 punya sinyal runtime sensitif. Belum ada gold, kategori final,
card KB, smart-diff final seluruh tambahan, atau holdout; tanpa inferensi baru.
2.062 TYP/281 HN belum terpapar menurut identitas/nama/dependency, belum bebas klon.

Antrean HN 17.225 versi/16.018 pair selesai direkonsiliasi. 17.097 arsip berhasil,
16.922 versi berhasil dipindai; semua kegagalan dicatat. Batch penuh mencakup
batch pertama, jangan dijumlahkan. Stream dipilih 500 nama sebelum penyaringan,
387 pair direkonstruksi, 381 lolos; jangan pooling FPR tiga strata tanpa bobot.
Dua MAL baru di manifest Datadog (@subql/common 5.8.3, tensorlake 0.5.144) tidak
punya arsip dan endpoint registry versi tepat 404, sehingga pair MAL baru nol.

Interupsi/ekor nol dan 324 cache rusak dipulihkan dengan salinan/hash tersimpan;
4.465 tree scan lama cocok. Lihat recovery-20261013, jangan sembunyikan kejadian
atau mengganti status gagal. Delapan unit test terfokus lulus. Akuisisi selesai,
tidak ada proses ekspansi aktif. Evaluasi lama tidak diubah/dijalankan ulang.

Bahan gabungan review.typical-combined.jsonl dan review.hn-combined.jsonl,
serta annotation-template.combined.A/B.jsonl kosong, ada di direktori penuh.
Berikutnya anotasi A/B, verifikasi tujuan HN, normalisasi/gold evidence,
clustering gabungan dan split dev/test/KB, serta akuisisi MAL independen.
Jangan membuat label manusia otomatis atau menyebut studi Q1/RAG selesai.


## D96: clustering gabungan dan usulan partisi selesai, 13 Oktober 2026

Laporan docs/campaign-split-20261013.md; artefak data/acquisition/campaigns-20261013/.
Aturan D96: file < 64 byte setelah strip tidak menautkan kriteria (b); aturan lama
dijalankan sebagai sensitivitas. 27.493 item, nol kegagalan Dolos. Usulan: 274 dev,
1.896 calon test TYP (popular 704/random 814/stream 378), 250 HN calon holdout
menunggu anotasi A/B. split-proposal.jsonl adalah usulan; review.*.jsonl tidak
diubah (holdout_eligible di sana tetap false). Berikutnya: anotasi A/B HN (250
eligible lebih dulu), lalu split HN test/KB per kategori §3.3, akuisisi MAL
independen, bekukan matriks inferensi. Jangan membuat label gold sendiri.

## Audit lanjutan D96 selesai — 13 Oktober 2026

Pengguna membawa hasil kelanjutan Claude dan meminta lanjut. Audit penyebab
mega-klaster selesai: docs/campaign-audit-20261013.md. Aturan dan split D96
tidak berubah. Laporan+hash saja: 9.857 klaster, terbesar 1.870. Giant 12.269
berasal dari 1.996 komponen exact yang tersambung oleh Dolos; termasuk template
Next.js, aset umum, dan stub 77 byte. Ini klaster konservatif antikebocoran,
bukan bukti bahwa semuanya satu insiden. Metodologi §3.6 diselaraskan dengan
D96 bytes.strip(), tanpa ambang baru.

data/acquisition/campaign-audit-20261013/: 20.315 witness edges diverifikasi
(2.679 Dolos), pemetaan 27.493 item/7.178 klaster identik; 79 jalur ke item
terpapar; 128 contoh file/64 hash cocok; 11.912 input pin cocok; 15 unit test
dan campaign/runner selfcheck lulus. Sertifikat tidak mengulang seluruh Dolos
antar-klaster atau ambang 0,8. Tiga percobaan audit dihentikan untuk optimasi
resource; log dipertahankan. Tidak ada kerusakan/perubahan sumber yang dibuat
oleh audit ini. Semua container audit selesai, tanpa jaringan/kode paket.

data/acquisition/hn-annotation-20261013/: tepat 250 material sumber dan
annotation.A/B.jsonl kosong. Jangan menimpa setelah manusia mengisi. Bukan
smart-diff final, bukan gold, belum input runner. 3 calon holdout berbagi
kampanye dengan 12 item KB: daftar holdout-kb-exclusions.jsonl di direktori
audit harus diterapkan ketika membangun retrieval final. Tidak diterapkan
ke eksperimen lama. Berikutnya tetap normalisasi evidence, anotasi dua manusia,
HN split kategori/card, dan MAL independen; jangan menyatakan G1/G2 selesai.
