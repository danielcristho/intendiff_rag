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

## 14 Oktober 2026: runner D92 per model untuk pengguna

Pengguna menjalankan sendiri D92 lewat scripts/full-method/run_<tag>.sh (memanggil
run_model resmi, tanpa mengubah sumber beku). Status: qwen3/qwen25 lengkap+verified;
qwen25_7b, qwen3_8b, phi4_mini, llama31_8b, granite33_8b 0/2919. Cek ./status.sh.
D97 (Guo+RogueOne) sedang akuisisi: 54 kandidat pair Guo, 47 predecessor diekstrak,
10 predecessor ber-advisory; arsip v_t Guo/RogueOne masih diunduh.

## D98 — persiapan eksperimen akhir, 14 Oktober 2026

Pengguna meminta fokus pada eksperimen akhir sesudah dijelaskan D92 tidak
memuat MM/MB. Jangan menyebut D92 selesai sebagai seluruh penelitian selesai.
RAG utama tetap 6 konfigurasi × 2 model 3–4B menurut metodologi; tidak
memilih model berdasarkan TPR D92. Snapshot D92 tidak diubah. Pada awal
persiapan tidak ada proses D92/D97 aktif; status D92 terakhir KeyboardInterrupt
pada Qwen3-8B, bukan dihentikan oleh tahap persiapan ini.

Laporan docs/final-rag-preparation-20261014.md; artefak
data/preparation/final-rag-20261014/. 250/250 HN calon holdout dinormalisasi
offline dengan static-dolos-exact-v2, tanpa error pair. Hash/token cocok,
10 pin input cocok. Tetap ada 53 diff terpotong, 15 pair/74 file raw fallback,
6 intent tidak tersedia. Bahan annotation/materials.jsonl dan formulir A/B
kosong terikat diff_sha256 siap untuk manusia, belum gold atau test beku.
Template sebelumnya tidak ditimpa. Jangan mengisi label/card sebagai AI.

Guard baru pipeline/retrieval_audit.py dipanggil runner sebelum request/file
hasil: menolak komposisi card yang kurang, ID duplikat, metadata eksklusi
hilang, anchor MM/MB bergeser, atau card MB berubah ketika intent ditambahkan.
Sepuluh unit test + selfcheck runner/configs lulus. Final_readiness.py adalah
audit parsial input, selalu exit 2/launch_ready=false hingga validator rilis
semantik/provenance/G1/G2 terintegrasi; jangan menganggap flag gold boolean
sebagai bukti manusia atau mengubahnya menjadi true untuk melewati gate.

Kelima arsip D97 kini lengkap dan cocok ukuran/MD5 metadata Figshare;
SHA-256 ada di external-archive-verification.json. Belum diekstrak sebagai
pair malicious akhir: 54 kandidat Guo, 49 record predecessor/47 sukses,
10 advisory positif. Tiga ZIP besar memiliki 2.111.806 / 1.176.455 /
2.319.894 entry; perlukan ekstraksi selektif berbatas resource, jangan
mengekstrak semua atau menjalankan image RogueOne.

Belum ada test/KB final atau card manusia baru, inferensi RAG baru nol.
Berikutnya: hasil anotasi dua manusia (pengguna sudah ditanya lokasi jika
ada di luar repo), card A ditinjau B, ekstraksi selektif/validasi pair D97,
clustering/split final, eksklusi dependency, audit token semua arm/model,
validasi dev dan pembekuan G1/G2, lalu batch final yang cakupannya eksplisit.

## D99/D100 — beralih ke label sumber sesuai instruksi pengguna, 15 Oktober 2026

Pengguna menolak kewajiban dua anotator dan mengizinkan penanganan eksperimen
berbasis dataset. Jangan mengulang permintaan anotasi manusia sebagai prasyarat.
Protokol aktif docs/source-labelled-final-20261014.md; hasil/pembatasan di
source-labelled-results-20261015.md. MAL label sumber, TYP assumed-benign,
HN pending hanya alarm tanpa FPR. RQ2/RQ3 deskriptif MAL+TYP; tidak mengklaim
hipotesis FPR_HN lama selesai. G1/G2 sekarang berbasis sumber/split/format/pin.

Artefak data/preparation/source-labelled-20261014/ (nama berdasarkan mulai batch):
54 Guo target ditemukan, 53 identitas diekstrak, 43 pair lolos predecessor,
33 MAL/33 kampanye eligible setelah nama/paparan kampanye. 1.869 TYP test-candidate
(692 popular/801 random/376 stream), 50 M + 25 B KB deterministik; seluruh
nama/kampanye KB direservasi. 67 kandidat B attrition tercatat. Semua 33 MAL
terbit sebelum rilis kedua model, bukan bukti generalisasi temporal baru.
Acquisition-verification: 43 label cocok CSV, 86 arsip/tree cocok, 11.902 pin
kampanye cocok; incremental 27.536 item/7.212 klaster @0.5, old closure diwarisi.
RogueOne belum dipakai. Tidak ada label gold manusia atau kode paket dieksekusi.

Normalisasi 1.902 pair berjalan dalam container intendiff-d99-normalize,
output cohort/pairs.preprocessed.jsonl, log normalization.log. Jangan ubah
kode yang dipin normalization-input-pins.json selama proses. Dataset.py telah
memperbaiki hilangnya hash arsip saat checksum index tidak diberikan; membawa
provenance/strata, konflik hash ditolak. Jangan menimpa snapshot D92/D98 lama.

Dev awal data/evaluation/source-rag-20261015/ selesai: 120 respons diverifikasi,
JSON Qwen3 75%, Qwen2.5 78,33%, keduanya <90%. D100 memakai SATU revisi format
akhir user prompt: escape JSON benar, evidence <=1 baris pendek atau [], reason
<30 kata. System prompt, aturan keputusan dan 512 output token tetap. Live
pipeline/prompts.py sudah D100; snapshot awal utuh. Dev revisi sedang berjalan
(data/evaluation/source-rag-v2-20261015/), pipeline source_experiment.py dibekukan
di code/. Jangan mengubah snapshot saat proses aktif. Belum ada inferensi test.

scripts/source-rag/status.sh untuk status baru; status.sh root tetap D92.
source_freeze.py menolak test sampai dev lengkap dan JSON>=90% kedua model,
normalisasi lengkap, hash/provenance/split/budget lolos. Menambahkan semua nama
dependency berubah dari kedua manifest, bukan hanya tiga delta_evidence. Setelah
freeze, scripts/source-rag/run.sh test menjalankan 22.824 generasi Stage 1 jika
1902 pair tetap. source_report.py memerlukan semua hasil lengkap dan menghasilkan
TPR sumber/FPR per strata/akurasi cohort/balanced accuracy/CI serta paired delta.
Stage 2 belum dilaksanakan. Tidak mengklaim riset selesai hanya karena sumber
atau dev selesai. 21 tests terfokus lulus; selfcheck runner/configs/prompts lulus.

## D101 — kelanjutan 15 Oktober 2026

Dev D100 selesai tetapi gagal format: Qwen3 50/60, Qwen2.5 42/60. D101
mengganti larangan constrained decoding secara eksplisit sebelum test. Schema
uniform di pipeline/output_schema.py; runner menyimpan hash request lengkap
dan response ID/model. Snapshot dev aktif source-rag-v3-20261015, scripts
source-rag sudah menunjuk v3; v1/v2 tetap utuh. Input/token dev sama D100,
respons baru seluruhnya. Jangan jalankan verifier live D101 pada hasil v1/v2.

Normalisasi selesai 1.901 sukses dari 1.902 kandidat; satu TYP stream
@libav.js/variant-vp9-opus@6.5.7 timeout dua kali (retry memori lebih besar).
Eksklusi teknis eksplisit cohort/technical-exclusions.jsonl, kandidat asli
dipertahankan. source_freeze memeriksa bahwa eksklusi tepat mencakup kegagalan
timeout berulang; sukses/tidak hadir tidak boleh diam-diam dikeluarkan.
Target baru 22.812 generasi dari 1.901 pair jika audit konteks lolos.
22 tes sebelumnya lulus; dua regresi tambahan eksklusi teknis juga lulus.

Dev D101 selesai terverifikasi: Qwen3 60/60 valid, Qwen2.5 59/60 valid.
Keduanya lolos gate >=90%. Pemeriksaan freeze dijalankan; lihat
source-rag-v3-20261015/freeze.log dan protocol.json untuk status rilis nyata.
Jangan menyamakan dev lolos dengan test selesai. Normalisasi memiliki 96 diff
truncated, 38 pair/53 file raw fallback, 135 intent unavailable.

Freeze D101 SUKSES: 1.901 pair, 75 card, 22.812 generasi; audit issues=[],
max prompt 30.144 kedua model (+512 output <32.768). protocol.json test_released
true; model/prompt/card/test telah beku, jangan diedit atau dituning. Kode
source_report.py/analysis.py ikut disalin ke code/ dan dipin. Kandidat 1.902
tetap tersimpan, satu eksklusi teknis dijelaskan, tidak ada human gold.

Batch test + laporan diluncurkan di background dengan PID 1174328; file
source-rag-v3-20261015/final.pid dan final.log. Skrip run-final.sh menjalankan
run.sh test lalu frozen code/source_report.py hanya jika runner sukses.
Pantau scripts/source-rag/status.sh. Jangan meluncurkan batch kedua saat
proses masih aktif; lock melindungi, server 8101 milik batch ini. Jika terhenti,
periksa sebab sebelum resume. Hasil final results.md/summary.json baru dibuat
setelah 11.406 respons/model lengkap+verified. Jangan klaim riset/Stage 2 selesai.
24 tes terfokus lulus, satu tes integrasi laporan tambahan lulus (TPR/akurasi/
balanced accuracy/FPR/paired delta pada fixture diketahui), selfcheck analysis ok.

## 16 Oktober 2026 — D102 perluasan lima model RAG

D101 SUDAH SELESAI: 11.406 respons/model verified, Qwen3 JSON 95,6%, Qwen2.5
99,5%. results.md/summary.json tersedia di source-rag-v3-20261015. Jangan
menjalankan ulang atau mengubah prompt/data berdasarkan hasil itu.

Pengguna bertanya mengapa hanya dua model dan menyetujui melanjutkan lima
model tambahan: Qwen2.5-Coder-7B, Qwen3-8B, Phi-4-mini, Llama-3.1-8B,
Granite-3.3-8B. D102 mencatat pemilihan sesudah hasil utama diketahui. Enam
konfigurasi, 1.901 test, 10 dev, 75 card, prompt/schema/sampling tetap identik.
Target tambahan 57.030 test +300 dev; bukan menjalankan D92 tanpa retrieval.

Direktori baru data/evaluation/source-rag-extra-20261016/ per model. Persiapan
pipeline/extension_prepare.py (dua audit CPU sekaligus) memverifikasi bobot,
snapshot kode dari D101, menambahkan opsi chat/stop D92 ke hash request,
mengaudit semua token, menentukan konteks native/KV tanpa memangkas input.
Qwen3-8B enable_thinking=false; Granite thinking=false. Card tetap teks D101,
tokenizer baru boleh menghasilkan ukuran berbeda yang wajib dilaporkan.

Percobaan awal gagal pembacaan pins sebelum inferensi, disimpan di direktori
*-attempt-model-pins; reader diperbaiki memakai *.model-manifest.json D92
dan regresi kelima manifest lulus. Persiapan aktif lihat *.prepare.log.
Qwen25_7b dan qwen3_8b sudah siap konteks 32.768/KV6GiB. Dev qwen25_7b
dimulai terpisah (dev-launch.log); jangan bentrok GPU ketika meluncurkan batch.

scripts/source-rag/status.sh kini menampilkan tambahan lima model.
scripts/source-rag/run-extra.sh menjalankan pipeline/extension_batch.py:
semua dev dahulu, gate >=90% per model via extension_release.py, kemudian
test model yang lolos dan laporan frozen. Gagal satu model dicatat dan model
lain diteruskan. run-extra belum otomatis berjalan sebelum persiapan selesai
dan proses dev pertama keluar; cek proses/log nyata sebelum meluncurkan.
Jangan mengubah extension_batch/release/report atau kode persiapan yang
sudah dipin saat dev/inferensi aktif. Efektif konteks/cache juga dibekukan
di metadata sebelum prediksi pertama. comparison.md/json menggabungkan
ringkasan lengkap verified saja; saat ini baru 2/7, bukan angka estimasi.

Pembaruan: seluruh persiapan D102 selesai, preparation-errors.json=[].
Prompt test maksimum Qwen7B 30144, Qwen3-8B 30148, Phi 30306, Llama 30275,
Granite 37610. Konteks Granite 38912, model lain32768; KV semuanya6GiB.
Granite satu intent card67token (card248), teks dipertahankan, eksplisit D102.
30 tes terfokus lulus. Dev Qwen7B sudah menerima respons nyata.

Coordinator background SUDAH diluncurkan PID1705554 (lihat batch.pid/batch.log),
pipeline/extension_queue.py menunggu persiapan lalu lock dev Qwen7B, kemudian
exec extension_batch.py. Jangan meluncurkan batch kedua. Ia memproses seluruh
dev lalu test yang lolos dan comparison.md/json otomatis. Batch utama D101
tetap utuh. Cek status nyata; dev/input lolos belum berarti lima test selesai.

Dev pertama Qwen25_7b selesai VERIFIED 60/60, JSON100%, transport errors0.
Coordinator PID1705554 sudah exec extension_batch.py dan mulai urutan batch;
label dev_running pertama mencakup pemeriksaan/resume, 60 respons lama tidak
diulang. Seluruh sumber helper yang sudah dipin jangan diedit saat batch aktif.

Pengguna menanyakan batch terlihat tidak maju. Pemeriksaan: PID1705554 masih
aktif; Qwen7B dan Phi dev60/60 valid100%, test_ready. Qwen3-8B gagal gate dev:
49/60 valid81,67%, 9 finish_reason=length pada512token, 2 JSON tab mentah;
transporterrors0. Testnya sengaja tidak dirilis, jangan menurunkan threshold
atau mengubah frozen prompt/parser untuk meloloskan. Llama sedang startup
dev (server PID1718214 saat diperiksa), Granite menunggu. Skrip semua dev
dahulu lalu test model yang lolos; karena itu counter test masih0.
source_status.py (tidak dipin) diperjelas: gate PASS/FAIL, urutan, PID aktif,
model aktif dan elapsed. Tidak mengubah kode eksperimen/snapshot yang dipin.

## 16 Oktober 2026 — D103 tambahan MAL

Pengguna meminta menambah MAL, lalu menawarkan bantuan download. Unduhan tidak
terhalang: Guo empat ZIP dan RogueOne ro.tar.gz sudah ada; tidak perlu meminta
pengguna mengunduh ulang. Datadog diperbarui TERPISAH pada commit
8a74a4c8ee0e1a2927f0419e0710968702ded609 di data/upstream/datadog-20261016/.
Kategori compromised npm naik dari1.438 menjadi1.443versi. Lima target dan lima
pendahulu berhasil diunduh/diperiksa statis. Tensorlake gugur karena pendahulu
0.5.143 ber-advisory MAL-2026-17650. @subql/common gugur karena Dolos0,60414
terhubung klaster lama. Tiga versi @memtensor/memos-cloud-openclaw-plugin lolos
sebagai CALON evaluasi tambahan, tetapi semuanya SATU kampanye MAL-2026-16476.
Test utama tetap33MAL; tidak mengubah data/prompt/model D101/D102 atau inferensi.

Artefak data/acquisition/mal-expansion-20261016/. Clustering otoritatif berada
di campaigns-with-exposure/, mewarisi27.536item D99 (bukan D96), blok seluruh
pool lama dan exposure registry termasuk dependency serta test/dev/KB D101.
campaigns/ adalah pemeriksaan awal pool saja; hasil sama tetapi gunakan versi
with-exposure. acquisition-verification.json lulus, pairs.manifest.jsonl3pair.
Preprocessing pertama gagal3/3 karena container static-v2 tidak punya tokenizers;
retry SUDAH SELESAI3/3sukses, nolrawfallback, dengan mount .venv/lib/python3.12/site-packages
read-only sebagai /python-deps dan PYTHONPATH=/python-deps. Cek
preprocessing-retry.log dan baris sukses terakhir perID pada pairs.preprocessed.jsonl;
baris gagal lama sengaja dipertahankan. preparation-verification.json lulus,
source trees tidak berubah. Belum ada test baru dirilis; perlu protokol evaluasi
terpisah dan audit konteks konfigurasi/model sebelum inferensi tambahan.

RogueOne sudah diinventaris sebagai TAR, image TIDAK dimuat/dijalankan:
337.440entri antar-layer, RO/Samples berupa benign dan tests berupa fixtures.
Tidak menafsirkan fixture sintetis sebagai MAL nyata. Belum ada tambahan MAL
sah dari sumber ini. Laporan docs/mal-expansion-20261016.md, keputusanD103.
Helper baru mal_refresh.py, mal_refresh_pairs.py, archive_layers.py,
mal_expansion_campaign.py, mal_expansion_verify.py; empat tes baru dan sembilan
tes ekspansi lama lulus. Semua kode lama yang dipin tetap utuh, belum commit.
Menambah satu kampanye belum menyelesaikan kekurangan keragaman. Jika mencari
sumber berikutnya, prioritaskan arsip pair MAL nyata/pendahulu yang tersedia,
bukan paket malicious-from-birth atau pengulangan versi kampanye sama.

## 17 Oktober 2026 — D104, 96 calon MAL /65 kampanye

Pengguna meminta melanjutkan penambahan menuju sekitar100kampanye. Batch baru
SELESAI akuisisi+preprocessing di data/acquisition/mal-expansion-20261017/.
96calonpair/65kampanye mencakup3pair/1kampanyeD103; tambahan bersih93pair/64kampanye.
Bersama test utama33pair/33kampanye =>129pair/98kampanye menurut closure baru,
tanpa irisan kampanye. Ini BUKAN129test yang sudah dievaluasi. Test tambahan
belum dirilis, belum ada inferensi, D101/D102 utuh. Sasaran100bukan kuota untuk
melonggarkan aturan atau memasukkan dua kasus meragukan.

Draz DOI10.1038/s41598-026-71750-5, Zenodo22057621, artefak429.595byte disimpan
di data/upstream/draz-20261016/ dan cocok checksumZenodo. Identitas versi dipakai
sebagai petunjuk, bukan label final; target dikonfirmasi MAL-OSV, pendahulu dihitung
ulang dari registry dan harus clear sumber MAL/advisory. 3.344recordnpm ->2.050leads
pada984nama baru ->395pasangan metadata ->159clearadvisory ->317/318arsipvalid
->156pairterekstrak. Digabung4pairD103 ->160;31hubungpoollama+33capkampanyegugur
->96ready. Clustering memakai helper D103 (tidak diedit), seluruh fingerprint
baru/lama dicek, inheritsD99 27.536item, bloktest/dev/KB dan dependencyexposure.

pairs.manifest.jsonl96; pairs.prepared.jsonl96kanonik; acquisition-verification.json
dan preparation-verification.json verified. 96/96preprocessing sukses;2file
rawfallback(66o index.js,svharness template.ejs),8difftruncated sesuaiaturanlama.
75pairterbit2026. Label target source-labelled, ketiadaan advisory pendahulu
bukan goldbenign atau bukti takeover. Belum ada anotasi manusia baru.

Laporan docs/mal-expansion-20261017.md; keputusanD104. Helper baru mal_leads.py,
mal_lead_archives.py,mal_holdout_verify.py,mal_preparation_verify.py;8tesMAL lulus.
Seluruh ekstraksi/normalisasi/clustering offline; hanya arsip/metadata trusted
source diunduh. Sumber notebook/kodeDraz tidak dijalankan. Belum commit.

Jalur tambahan yang sudah dicoba: Guo548pendahuluunik ->84clearadvisory ->84HTTP404,
nolrecovery. Incidentcorpus164manifestdipin, beberapa payload-only/rekonstruksi/
endpointprivat tidakdipakai. Tiga petunjuk baru flatmap-stream/faker/react-native-
international-phone-number tidaklolos ketersediaan/konfirmasiMAL. Jangan mengulang
unduhan Guo/RogueOne atau mengklaim arsipbesar berarti lebihbanyakpairlayak.

Langkah berikut bila diminta mengevaluasi: protokol/snapshot TERPISAH untuk
96calonbaru, audit seluruh konteks tiapkonfigurasi/model, lalu rilis sebelum
inferensi. Script source-rag lama masih menunjuk test1.901; tidak otomatis
mencakup96tambahan ini. Jangan mengubah prompt/KB berdasarkan hasil test.

## 18 Oktober 2026 — D105 evaluasi MAL tambahan dilepas ke background

Pengguna meminta menjalankan semua evaluasi yang aman lalu mengakhiri sesi chat
untuk hemat token; tidak perlu menunggu seluruh inferensi selesai. Tidak melakukan
fine-tuning. Hasil D101/D102 sudah diverifikasi ulang: enam model lengkap11.406test
per model. Qwen3-8B tetap gagal dev49/60valid81,67%, tidak boleh masuk test.

Persiapan D105 SELESAI tanpa error di data/evaluation/source-rag-mal-20261018/.
96MAL/65kampanye D104, enam arm D101 termasukMM/MB,576respons/model, total3.456.
Enam model eligible qwen3,qwen25,qwen25_7b,phi4_mini,llama31_8b,granite33_8b.
Dev60respons/model dipakai ulang dengan verifikasi hash request/token persis;
KB/prompt/schema/parser/options/bobot tetap. Semua input/context diaudit. Granite
promptmaks35.438, context36.864; lainnya context32.768. KV6GiB semuanya. Tidak
mengulang test lama. Semua sumber inference dibandingkan byte-for-byte dengan
parent kecuali driver kapasitas konteks yang mengikuti aturanD102.

Batch dilepas memakai subprocess.Popen(start_new_session=True), stdinDEVNULL,
stdout/stderr batch.log. PID awal3570758 (cek batch.pid dan/proc sebelum menganggap
masih aktif). Model berjalan berurutan, verifier+laporan otomatis per model.
Pemeriksaan16tes lulus (11MAL+5extension). Tidak ada packagecode dijalankan.

Cek scripts/source-rag/status-mal.sh; status.sh lama juga menampilkan tambahan.
Resume bila perlu scripts/source-rag/run-mal.sh; lock mencegah batch ganda,
respons sukses dilewati. completion.json membedakan selesai semua vs gagal.
Jangan mengubah helper mal_eval_prepare/batch/report/metrics, extension_audit,
extension_prepare, dokumenprotokol docs/mal-evaluation-20261018.md atau input
yang dipin selama batch. Semua belum di-commit; banyak perubahan lama tetap.

Pelaporan: TPR96MAL tambahan terpisah dari33MAL lama; CI95bootstrapkampanye10.000
seed2026, invalidbenignutama/malicioussensitivitas. FPR/BA tidak terdefinisi untuk
batch MAL-only. summary.json memuat hasil lama+gabungan129MAL/1.868TYP hanya
deskriptif; FPR menggunakan TYP lama. Jangan menyebut129freshholdout atau11riburespons
sebagai jumlahpair. Rencana lengkap docs/mal-evaluation-20261018.md, keputusanD105.

Sebelum mengakhiri sesi, batch dipastikan masih aktif dan Qwen3 sudah menghasilkan
45/576respons test. Verifier snapshot memeriksa45respons tersebut: hash request,
token, identitas, retrieval dan parsing cocok; transporterrors0, JSON44/45valid.
Ini pemeriksaan awal, bukan hasil final atau jaminan semua model selesai. Lima
model lain masih antre. Pengguna akan mengabari setelah selesai; jangan menunggu
batch sampai tuntas dalam sesi ini.

## 18 Oktober 2026 — batch selesai dan naskah ditulis ulang

Pemeriksaan berikutnya memastikan D105 complete=true: keenam model eligible
576/576 verified, transport errors0; Qwen3-8B tetap gagal gate dev. Tidak ada
batch yang masih perlu ditunggu. Pengguna kemudian meminta penulisan ringkas,
objektif, berdasarkan eksperimen, dengan gaya paper jurnal.

Naskah aktif labs/latex/intendiff-rag.tex telah ditulis ulang lengkap mengikuti
D99/D101/D102/D105 dalam Bahasa Indonesia. PDF labs/latex/intendiff-rag.pdf
berisi sembilan halaman: satu highlights dan delapan naskah/lampiran/referensi.
Abstrak, metode, hasil, pembahasan, keterbatasan, kesimpulan terisi; tidak lagi
memuat hasil eksploratori lama atau menjanjikan anotasi ganda/FPR_HN/stabilitas
yang belum dilakukan. File lama results-exploratory/discussion-exploratory dan
file Inggris kosong tetap ada. Backup source sebelumnya di
data/writing/paper-20261018/previous/. Semua belum commit.

pipeline/paper_results.py dan paper_tables.py menghasilkan lima tabel dan
grafik tiga kontras dari hasil tersimpan. Audit mencocokkan coverage/identitas,
confusion kedua kebijakan invalid, akurasi/BA gabungan, token dan latensi untuk
71.892respons/1.997pair. CSV dan verification.json dengan pin sumber berada di
data/writing/paper-20261018/. Tidak ada inferensi baru. Dua tes exporter lulus.

Hasil ditulis apa adanya: MM→MB meningkatkan FPR pada empat model; dua model
dengan FPR turun juga kehilangan TPR tambahan. Pada estimasi titik, tidak ada
perbaikan bersama untuk keenam model. Semua CI tetap deskriptif, bukan hipotesis
konfirmatori atau kesimpulan universal. Label sumber, cohort pascahasil awal,
clustering proksi, truncation, output invalid dan cache dijelaskan.

Audit lengkap docs/manuscript-audit-20261018.md, instruksi labs/latex/BUILD.md.
Build selesai tanpa referensi/sitasi undefined; tabel/plot diperiksa visual.
Satu warning CAS berasal dari kotak keyword nol-lebar dan tidak memotong teks.
TeX dependencies sementara di /tmp/intendiff-texmf, -var, -config. Metadata
penulis, deklarasi faktual, venue dan URL rilis publik belum tersedia, tidak
dikarang. Mode doubleblind/footer Draf penelitian digunakan sementara.

### Revisi struktur naskah sesuai arahan pengguna

Semua label RQ dan subbagian Pertanyaan penelitian dihapus dari naskah aktif.
Pendahuluan memakai tujuan deklaratif; kontribusi penelitian menjadi tiga poin
bernomor. Preferensi pengguna: tidak memakai struktur RQ dalam paper. PDF
dibangun ulang dan daftar kontribusi diperiksa visual; tetap 9 halaman total.
Angka eksperimen tidak berubah. Pin sumber TeX dan PDF diperbarui.
