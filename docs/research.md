# Desain penelitian

Revisi 2026-09-13. Dokumen ini menggantikan research gap dan RQ di proposal P1
(slide 8–10 dan 15). Alasan tiap perubahan ada di [decisions.md](decisions.md);
prosedur lengkap (data, prompt, konfigurasi, statistik) ada di [methodology.md](methodology.md).

## 1. Masalah

**Serangan yang disasar:** update pada paket yang sudah dipercaya menyisipkan
payload. Contoh motivasi untuk naskah:

- **chalk, debug, dan 16 paket lain** (September 2025). Kredensial maintainer diperoleh
  lewat rekayasa sosial; payload diam-diam memanipulasi transaksi kripto. Gabungan
  unduhan paket-paket itu sekitar dua miliar per minggu.
- **Worm Shai-Hulud** (sepekan setelahnya). Mencuri token npm dan kredensial lain,
  lalu menerbitkan versi terinfeksi dari paket lain milik maintainer yang sama.
  Lebih dari 180 paket terkompromi dalam 24 jam pertama.
- **axios@1.14.1 dan axios@0.30.4** (31 Mar 2026). Menambahkan dependency
  `plain-crypto-js` yang mengunduh dan menjalankan RAT saat instalasi.

CVE-2025-66478 (Next.js, slide 3) **tidak dipakai** sebagai contoh update
berbahaya. Itu kerentanan (React2Shell) di kode yang sah. Kasus itu boleh dipakai
sebagai kontras: `npm audit` menangkapnya karena advisory-nya sudah terbit,
tetapi tidak menangkap update berbahaya yang belum punya advisory.

**Kenapa sulit:** API yang dipakai malware (network, `child_process`, `process.env`,
install hook, obfuscation) juga dipakai paket sah. Guo et al. (2026) menyimpulkan
bahwa setiap detektor harus menyelesaikan ambiguitas antara *capability* dan *intent*.

**Kenapa false positive penting:** npm menerima sekitar 15 update per menit
(Wyss et al., mengutip Sandworm), atau sekitar 21.600 per hari. Setiap 1% FPR
berarti sekitar 216 alarm palsu per hari.

**Posisi:** triage update dependensi pada jendela sebelum advisory terbit,
dengan model lokal sehingga kode tidak dikirim ke pihak ketiga.

## 2. Posisi terhadap penelitian terkait

| Penelitian | Yang sudah dilakukan | Yang belum | Hubungan dengan penelitian ini |
|---|---|---|---|
| **Wyss et al., RAID 2025 — referensi utama** | Smart-diff update + GPT-4o, GPT-4-Turbo, Gemini-2.0-Flash; GPT-4o mendeteksi 46/46 update malicious dengan 8/2.000 false positive | Model kecil lokal, intent, retrieval, stabilitas antar run | Tugas dan input sama. Kami mengganti model dan menambah intent serta retrieval contrastive |
| IntelGuard (Guo et al., WWW '26) | RAG dari 8.000+ halaman laporan threat intel; menilai kesesuaian perilaku dengan fungsi paket; GPT-4.1-mini; paket utuh | KB berisi contoh malicious saja; bukan level update; model tertutup | E3 adalah retrieval ala IntelGuard; E4 menguji tambahan benign look-alike |
| Guo et al., arXiv 2603.27549 | Benchmark 6.420 malicious + 7.288 benign; 11 tool / 16 varian | — | Bukti masalah capability vs intent; sumber kandidat hard negative |
| RogueOne (Sofaer et al., ICSE 2024) | Differential data-flow dengan trust domain; 75,6% deteksi, 4,7% FP pada dataset single-update | — | Pembanding non-LLM; dikutip, tidak dijalankan ulang |
| SocketAI (Zahan et al., ICSE 2025) | GPT-3/GPT-4 pada 5.115 paket | Model kecil; level update | Related work LLM + npm |
| Nguyen et al., arXiv 2512.12313 | Taint slicing + DeepSeek-Coder 6.7B pada paket utuh, akurasi 87,04% | Level update; model 3–4B | Pesaing terdekat untuk Gap 1, harus dibedakan secara eksplisit |
| CHABADA (Gorla et al., ICSE 2014) | Membandingkan deskripsi app Android dengan perilaku API-nya | npm; LLM | Akar konsep intent mismatch |
| Gao & Das, AAAI 2024 | Contrastive in-context learning (contoh positif + negatif) | Domain keamanan | Akar konsep contoh pembanding |
| Froh et al., SCORED 2023 | Analisis statis diferensial (CodeQL) antarversi; rata-rata 1,3% alarm palsu | LLM, intent | Pendahulu non-LLM di level update |
| Vul-RAG (Du et al., TOSEM 2026) dan replikasinya (Kaniewski et al., 2026) | RAG pengetahuan untuk kerentanan; LLM sulit membedakan kode rentan dari tambalan yang mirip; pada model open-weight akurasi berpasangan tertahan di sekitar 0,30 | Paket npm | Bukti bahwa kasus "mirip tapi aman" sulit dan manfaat RAG bagi model open-weight tidak dijamin |

Tabel positioning lengkap untuk naskah ada di `labs/latex/intendiff-rag.tex` (Tabel `tab:positioning`).

## 3. Research gap (revisi)

Klaim di bawah berlaku sejauh penelusuran kami per 2026-09-13.

- **Gap 1 — model 3–4B pada smart-diff update belum dievaluasi.** Wyss et al.
  memakai model tertutup; Nguyen et al. memakai model 6.7B pada paket utuh.
- **Gap 2 — belum ada evaluasi retrieval dengan contoh benign pembanding** untuk
  deteksi paket npm berbahaya. KB IntelGuard hanya berisi contoh malicious.
  **Ini klaim kebaruan utama.**
- **Gap 3 — efek intent eksplisit belum diukur secara terkontrol.** Ide
  membandingkan perilaku dengan fungsi paket *bukan* ide baru (CHABADA 2014;
  IntelGuard secara implisit). Kontribusinya adalah pengukuran lewat ablation
  pada hard negative, bukan idenya.

**Kontribusi yang realistis:** evaluasi level update untuk model 3–4B, ablation
terkontrol untuk contoh benign dan intent, serta subset hard negative, skema
knowledge card, dan protokol label yang dapat direplikasi.

## 4. Pertanyaan penelitian

### Notasi

- **MAL, HN, TYP**: subset update malicious, hard negative, dan typical ([methodology.md §3](methodology.md#3-data)).
- **FPR_HN(E)**: proporsi pair HN yang diberi verdict `malicious` oleh konfigurasi E. FPR_TYP didefinisikan sama untuk TYP.
- **Recall(E)**: proporsi pair MAL yang diberi verdict `malicious` oleh konfigurasi E.
- Semua perbandingan bersifat **paired**: pair sama, model sama, dan hanya satu faktor yang berbeda.

### RQ1 — Kemampuan dasar model kecil (Gap 1) · deskriptif

> Seberapa akurat LLM open-weight 3–4B mendeteksi update npm berbahaya dari
> smart-diff tanpa contoh, diukur dari recall serta FPR pada update typical dan
> hard negative?
>
> *How accurately do 3–4B open-weight LLMs detect malicious npm updates from a
> smart-diff without examples, in terms of recall and false-positive rate on
> typical and hard-negative updates?*

- **Konfigurasi:** E0-noint (smart-diff saja) dan E0 (smart-diff + intent).
- **Ukuran:** Recall, FPR_TYP, dan FPR_HN dengan Wilson 95% CI, per model.
- **Kenapa bukan "apakah model kecil cukup?":** tidak ada ambang "cukup" yang
  disepakati. Kalau ambangnya kami tetapkan sendiri, jawabannya bergantung pada
  ambang itu, bukan pada data.
- **Kenapa angka Wyss et al. tidak masuk rumusan RQ:** prompt, implementasi, dan
  sampelnya berbeda, dan GPT-4o tidak dijalankan ulang, sehingga selisihnya tidak
  bisa diuji. RQ hanya menjanjikan apa yang bisa dijawab dengan data sendiri.
  Perbandingan dengan Wyss dibahas di Diskusi ([§5, aturan klaim](#aturan-klaim)).
- **Bentuk jawaban:** "Qwen3-4B (E0-noint): recall a% [CI], FPR_TYP b% [CI],
  FPR_HN c% [CI]." Di Diskusi, FPR boleh diterjemahkan ke beban operasional
  (§1: setiap 1% FPR ≈ 216 alarm palsu per hari).

### RQ2 — Confirmation bias dan contoh pembanding (Gap 2) · uji hipotesis

**RQ2a**

> Apakah menyertakan contoh malicious hasil retrieval menaikkan FPR pada hard
> negative dibanding zero-shot?
>
> *Does adding a retrieved malicious example increase the false-positive rate
> on hard negatives compared with zero-shot?*

**H2a:** FPR_HN(E3) > FPR_HN(E0).

**RQ2b — hipotesis utama**

> Dengan jumlah contoh yang sama, apakah mengganti satu contoh malicious dengan
> satu benign look-alike menurunkan FPR pada hard negative tanpa menurunkan
> recall lebih dari 5 poin?
>
> *Holding the number of examples fixed, does replacing one malicious example
> with a benign look-alike reduce the false-positive rate on hard negatives
> without lowering recall by more than 5 points?*

**H2b:** FPR_HN(E4) < FPR_HN(E3-k2), **dan** Recall(E4) − Recall(E3-k2) ≥ −5 poin.

- **Kenapa E3-k2, bukan E3:** E4 berisi 2 contoh. Tanpa kontrol dengan 2 contoh,
  penurunan FPR bisa berasal dari jumlah contohnya.
- **Kenapa FPR_HN, bukan F1:** F1 bergantung pada rasio kelas di dataset.
  Mekanisme yang diuji (contoh benign mengurangi kecenderungan menuduh) bekerja
  pada benign yang mirip malicious.
- **Kalau H2a tidak didukung:** RQ2b tetap sah. Hanya narasi "menekan confirmation
  bias" yang diganti menjadi "menurunkan FPR".

### RQ3 — Intent paket (Gap 3) · uji hipotesis

> Apakah menyertakan intent profile paket (deskripsi, README, dan scripts dari
> versi sebelumnya) menurunkan FPR pada hard negative tanpa menurunkan recall
> lebih dari 5 poin?
>
> *Does providing an explicit package intent profile (description, README, and
> scripts from the previous version) reduce the false-positive rate on hard
> negatives without lowering recall by more than 5 points?*

**H3:** FPR_HN(E4) < FPR_HN(E4-noint), **dan** Recall(E4) − Recall(E4-noint) ≥ −5 poin.

Pembanding sekunder tanpa uji: E0 vs E0-noint, yaitu efek intent tanpa retrieval.

### RQ4 — Biaya · deskriptif

> Berapa tambahan token, latency (median dan p95), dan memori GPU yang dibutuhkan
> setiap komponen — intent, retrieval, dan contoh kedua — pada dua model 3–4B,
> dan konfigurasi mana yang tidak didominasi konfigurasi lain?
>
> *What does each component — intent, retrieval, and the second example — add in
> tokens, median and p95 latency, and GPU memory on two 3–4B models, and which
> configurations are Pareto-optimal?*

- **Biaya komponen** dihitung sebagai selisih antar pasangan konfigurasi:
  - E0-noint → E0: intent
  - E0 → E3: satu card
  - E3 → E3-k2 atau E4: card kedua
- **Pareto front** dihitung pada (FPR_HN, Recall, median latency).
- Memori GPU dilaporkan sebagai memori minimum terhitung per model: memori bobot dari log vLLM ditambah KV cache terhitung ([methodology.md §9.3](methodology.md#93-kebutuhan-memori-dan-cara-mengukurnya)). Puncak nvidia-smi tidak dipakai (D41). Model GPU, total VRAM, dan dtype dilaporkan.

### Analisis eksploratif

Bagian ini tidak diuji signifikansinya dan dilaporkan sebagai deskripsi.

| ID | Analisis | Catatan |
|---|---|---|
| EA1 | FPR_HN per kategori hard negative, E4 vs E3-k2 | Menggantikan H1 proposal. H1 lama menyebut kelima kategori HN sekaligus, jadi tidak mungkin salah. Dengan ~20 pair per kategori, hasilnya hanya deskriptif |
| EA2 | Stabilitas: persentase pair yang verdict-nya berubah antar 3 run sampling (temperature 0,7) untuk E0 dan E4 | Menjawab limitasi Wyss soal stabilitas berulang |
| EA3 | Recall dan FPR pada insiden yang terbit sebelum vs sesudah tanggal rilis model | Mengukur risiko kontaminasi pretraining; mendukung "bertahan pada temporal split" (slide 17) |
| EA4 | Taksonomi error (capability, intent, retrieval) untuk semua kesalahan E4 | Dikerjakan di UI audit |
| EA5 | Evidence localization: proporsi true positive yang evidence-nya menunjuk baris malicious di gold | Butuh anotasi baris malicious pada MAL |

## 5. Decision rule

Aturan ini **dibekukan di Gate G2**, sebelum run pertama pada test set.

### Prosedur uji

1. H2a, H2b, dan H3 diuji per model, jadi ada **6 uji konfirmatori**.
2. **McNemar exact dua sisi** pada subset HN. Outcome per pair: diberi verdict
   `malicious` atau tidak.
3. **Koreksi Holm–Bonferroni** atas 6 uji, dengan α keluarga = 0,05.
4. **Selisih recall** dihitung paired, dengan 95% CI dari bootstrap 10.000 resample.
   Resampling dilakukan **per kampanye**, karena pair dari kampanye yang sama
   saling berkorelasi.
5. **Output tidak valid** (JSON gagal di-parse atau request error) dihitung
   sebagai verdict `benign` (fail-open, sama seperti RogueOne memperlakukan
   error). Analisis sensitivitas menghitungnya sebagai `malicious`. Keduanya
   dilaporkan.

### Label hasil untuk H2b dan H3

| Label | Syarat |
|---|---|
| **Didukung** | FPR_HN turun, p_Holm < 0,05, estimasi titik penurunan recall ≤ 5 poin, **dan** batas bawah CI selisih recall ≥ −5 poin |
| **Didukung sebagian** | FPR_HN turun, p_Holm < 0,05, dan estimasi titik penurunan recall ≤ 5 poin, tetapi batas bawah CI < −5 poin (recall aman belum terbukti) |
| **Arah sesuai, tidak signifikan** | FPR_HN turun, p_Holm ≥ 0,05, dan estimasi titik penurunan recall ≤ 5 poin |
| **Tidak didukung** | FPR_HN tidak turun, **atau** estimasi titik penurunan recall > 5 poin |

H2a tidak punya syarat recall. Labelnya **Didukung** (FPR_HN(E3) > FPR_HN(E0)
dengan p_Holm < 0,05), **Arah sesuai, tidak signifikan**, atau **Tidak didukung**.

### Aturan klaim

- Klaim umum, misalnya "benign look-alike menurunkan FPR pada model 3–4B", hanya
  boleh ditulis jika **kedua model** berlabel Didukung atau Didukung sebagian.
- "Tidak signifikan" **bukan** bukti bahwa tidak ada efek. Batas deteksi desain
  ini dijelaskan di [methodology.md §11.3](methodology.md#113-batas-yang-bisa-dibuktikan).
- **Kriteria adopsi** (revisi slide 15 dan 17): E4 direkomendasikan hanya jika H2b
  dan H3 berlabel Didukung atau Didukung sebagian pada kedua model, arah efeknya
  sama pada subset pasca-rilis (EA3), dan biaya RQ4 dilaporkan.
- Jika jumlah pair suatu subset di bawah minimum pada Gate G1, RQ yang bergantung
  pada subset itu dilaporkan secara deskriptif saja.
- **Angka penelitian lain** (Wyss et al., RogueOne, IntelGuard) hanya dibahas di
  Diskusi sebagai konteks, dengan menyebut perbedaan model, prompt, dan dataset.
  Tidak ada klaim "lebih baik" atau "lebih buruk" dari perbandingan lintas setup.
  Kalau data Wyss di OSF bisa dipakai, angka kita pada subset yang sama boleh
  disajikan berdampingan dengan angka mereka, tetap tanpa uji (D23).

## 6. Ancaman validitas

**Internal**

- *E4 punya lebih banyak contoh daripada E3.* Mitigasi: kontrol E3-k2.
- *Capability delta kosong pada serangan tersamar,* yaitu payload yang memakai capability yang sudah ada di v_{t−1}. Pada pola ini (CC-Harvest), RogueOne default melewatkan 10 dari 10 kasus. Retrieval berbasis delta tidak mendapat sinyal pada pair seperti itu. Mitigasi: recall dilaporkan terpisah untuk pair MAL dengan delta kosong.
- *Recency bias: card terakhir memengaruhi verdict.* Mitigasi: urutan card E4 di-counterbalance per pair.
- *Kualitas retrieval tidak simetris; pool benign lebih kecil sehingga card benign bisa kurang mirip.* Mitigasi: skor kemiripan setiap card dicatat dan dilaporkan per konfigurasi.
- *System prompt memberi petunjuk kategori HN.* Mitigasi: daftar kategori dihapus dari prompt (D17).
- *Prompt disetel sampai menang pada test set.* Mitigasi: desain dibekukan di G2; smoke test hanya pada dev set yang terpisah.
- *Penyerang mengendalikan README di versi baru.* Mitigasi: intent diambil dari v_{t−1}.

**Konstruk**

- *"Benign" pada HN berarti tidak ada advisory dan tujuannya terdokumentasi, bukan bukti mutlak.* Mitigasi: kriteria tertulis, dua anotator, dan Cohen's κ.
- *TYP diasumsikan benign.* Ini mengikuti asumsi Wyss et al.
- *Smart-diff bisa terpotong dan kehilangan konteks.* Mitigasi: flag `truncated` dianalisis sebagai subgroup.

**Eksternal**

- Kedua model berasal dari satu keluarga (Qwen), jadi klaim dibatasi pada model yang diuji.
- Hanya npm. MAL didominasi insiden lama (Backstabber's Knife Collection) ditambah beberapa kampanye 2025–2026.
- Batas maksimal 3 pair per kampanye mengurangi bias kampanye, tetapi juga membatasi n.

**Kontaminasi pretraining**

- Insiden terkenal kemungkinan ada di data latih model, dan nama paket terlihat di prompt.
- Mitigasi: EA3 membandingkan insiden sebelum dan sesudah tanggal rilis model. Tanggal rilis diambil dari model card dan dicatat di decisions.md.

**Kesimpulan statistik**

- *n kecil, sehingga efek kecil tidak terdeteksi.* Batas deteksi dilaporkan eksplisit.
- *Banyak perbandingan.* Hanya 6 uji konfirmatori dengan koreksi Holm; sisanya eksploratif.
- *Pair dari satu kampanye berkorelasi.* Mitigasi: bootstrap per kampanye.

## 7. Di luar cakupan

- Membandingkan langsung dengan RogueOne atau IntelGuard pada data yang sama.
- Ketahanan terhadap obfuscation adversarial. Wyss et al. §V-C sudah menunjukkan celahnya.
- Ekosistem selain npm, fine-tuning, model tertutup, dynamic analysis, dan tool produksi.
