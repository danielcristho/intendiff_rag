# Perbandingan hasil baseline dengan literatur — 29 September 2026

Belum ada bukti bahwa eksperimen ini mengungguli paper utama. Ada perbaikan
deskriptif ketika intent ditambahkan pada Qwen3 di korpus gabungan, tetapi
efeknya tidak konsisten pada Qwen2.5 maupun subset MAL dari Wyss.

Perbandingan ini memakai 3.892 respons yang sudah selesai; tidak ada panggilan
LLM tambahan, perubahan prompt, atau uji hipotesis. Metrik lokal menggunakan
label sumber MAL, asumsi benign untuk TYP, dan aturan invalid-as-benign D18.

## Konteks angka paper

Angka antarbaris berasal dari eksperimen berbeda, bukan pemeringkatan pada
benchmark yang sama. Recall dan FPR harus dibaca bersama.

| Studi / sistem | Recall malicious | FPR benign | Lingkup |
|---|---:|---:|---|
| Wyss, GPT-4o | 100% | 0,5%* | Pembaruan npm |
| Wyss, GPT-4-Turbo | 100% | 1,1%* | Pembaruan npm |
| Wyss, Gemini-2.0-Flash | 100% | 5,0%* | Pembaruan npm |
| RogueOne, default | 75,6% | 4,7% | Single-update: 41 malicious, 300 benign |
| IntelGuard, GPT-4.1-mini | 97,67% | 0,20% | Paket npm utuh dengan retrieval |
| Eksperimen ini, Qwen2.5 DIFF | 80,64% | 45% | 873 MAL sumber, 100 TYP |
| Eksperimen ini, Qwen2.5 DIFF+I | 68,16% | 43% | 873 MAL sumber, 100 TYP |
| Eksperimen ini, Qwen3 DIFF | 47,88% | 6% | 873 MAL sumber, 100 TYP |
| Eksperimen ini, Qwen3 DIFF+I | 56,70% | 3% | 873 MAL sumber, 100 TYP |

Sumber primer: [Wyss, Tabel II–III](https://ldklab.github.io/assets/papers/raid25-llmdetection.pdf),
[RogueOne, Tabel 2](https://www.cs.columbia.edu/~junfeng/papers/rogueone-icse24.pdf),
[IntelGuard, Tabel 2 dan §5.4](https://arxiv.org/html/2601.16458v1).

*FPR Wyss di atas dihitung sebagai 100% dikurangi specificity yang dilaporkan,
dengan sampel pelatihan classifier keluaran dikeluarkan. Hitungan mentah pada
seluruh 2.000 TYP adalah 8, 16, dan 75 FP, yaitu 0,40%, 0,80%, dan 3,75%.
Kedua penyebut ini tidak boleh dicampur. Paper melaporkan 46/46 MAL terdeteksi.

SocketAI melaporkan precision 99% dan F1 97% pada GPT-4. Metrik tersebut bukan
recall atau FPR dan tidak dibandingkan langsung dengan persentase deteksi kita.
Unit analisis dan rasio kelas juga berbeda.
[Sumber primer SocketAI](https://arxiv.org/abs/2403.12196v4).

Secara numerik, FPR Qwen3 DIFF+I di bawah angka RogueOne dan Gemini dalam tabel,
tetapi recall-nya juga lebih rendah. Ini bukan bukti keunggulan menyeluruh.
Begitu pula recall Qwen2.5 DIFF di atas angka RogueOne, tetapi FPR-nya jauh lebih
tinggi. Tidak ada klaim menang antarstudi yang dapat dibuat dari tabel ini.

## Perubahan internal yang benar-benar diamati

Semua selisih berikut dihitung dari pair yang sama pada DIFF dan DIFF+I.

| Model | Recall MAL DIFF → DIFF+I | Selisih | FPR TYP DIFF → DIFF+I | Selisih |
|---|---|---:|---|---:|
| Qwen2.5 | 80,64% → 68,16% | −12,49 poin | 45% → 43% | −2 poin |
| Qwen3 | 47,88% → 56,70% | +8,82 poin | 6% → 3% | −3 poin |

Untuk Qwen3, 157 MAL berubah dari tidak terdeteksi menjadi terdeteksi, sementara
80 berubah ke arah sebaliknya: bersih +77/873. Pada TYP, empat FP hilang dan satu
FP baru muncul: bersih −3/100. Penurunan FPR 50% relatif hanya berarti tiga
kasus bersih pada dataset ini, bukan bukti signifikansi atau generalisasi.

## Pemeriksaan khusus sumber Wyss

Dari 46 baris MAL sumber, satu pair tidak mempunyai kode lengkap dan dua pair
tidak lolos screening predecessor; tersedia 43 pair dalam evaluasi ini.
Asal paket sama tidak berarti preprocessing, prompt, classifier keluaran, atau
subset pengukuran identik dengan paper. Rinciannya ada pada
[persiapan data](real-data-20260928.md).

| Model | DIFF pada 43 MAL Wyss | DIFF+I pada 43 MAL Wyss | Selisih |
|---|---:|---:|---:|
| Qwen2.5 | 32/43 = 74,42% | 26/43 = 60,47% | −13,95 poin |
| Qwen3 | 31/43 = 72,09% | 26/43 = 60,47% | −11,63 poin |

Kenaikan agregat Qwen3 berasal dari bagian Datadog: 387/830 menjadi 469/830,
atau +9,88 poin. Pada subset sumber paper utama, penambahan intent belum
memberikan kenaikan. Ini analisis deskriptif setelah evaluasi, bukan hipotesis
baru yang telah dikonfirmasi.

## Batas interpretasi dan klaim yang dapat ditulis

[Audit ulang Qwen2.5](qwen25-audit-20260929.md) mengonfirmasi hitungan, tetapi
memperjelas interpretasinya: dari penurunan bersih 109 deteksi MAL, 104
melibatkan perubahan status valid/invalid dan hanya lima berasal dari
perubahan antar-verdict valid. Penurunan skor pipeline tidak boleh langsung
diartikan sebagai penurunan kemampuan memahami intent sebesar 12,49 poin.

Sebanyak 1.077/3.892 respons invalid: 520 mencapai batas 512 token, 525 gagal
sintaks JSON, dan 32 gagal skema. Karena semuanya dinilai benign, perubahan
metrik mencampurkan kemampuan mendeteksi dan kemampuan memenuhi format.
Jika invalid dinilai malicious, selisih recall Qwen3 mengecil menjadi +2,86
poin (85,57% → 88,43%); sensitivitas FPR berubah 14% → 12%.

Korpus MAL memiliki 224 klaster operasional dan satu klaster berisi 607/873
pair. Anotasi manusia, kuota test final, HN, dan konfigurasi retrieval belum
selesai. Karena itu, H2b/H3 utama serta manfaat contrastive RAG belum dapat
dinilai dari eksperimen ini.

Median request lokal 0,803–1,407 detik secara numerik lebih rendah daripada
median GPT-4o 9,07 detik pada Tabel IV Wyss. Namun hardware, input, keluaran,
caching, dan batas token berbeda; ini belum membuktikan percepatan sistem
menyeluruh atau biaya lebih rendah. Angka 9,91 detik di paper adalah rata-rata
query, bukan median query.

Rumusan hasil yang sesuai bukti: **Penambahan intent memperbaiki recall
berdasarkan label sumber dan FPR TYP pada Qwen3 dalam korpus gabungan, tetapi
efeknya bergantung pada model dan sumber data. Keunggulan terhadap metode
terdahulu serta manfaat retrieval belum dibuktikan.**

Artefak lokal: [hasil evaluasi](../data/evaluation/source-baselines-20260929/report.md),
[hitungan per sumber dan perubahan berpasangan](../data/evaluation/literature-comparison-20260929.json).
