# Protokol eksperimen

Revisi 2026-09-13. RQ dan decision rule ada di [research.md](research.md); alasan
perubahan dari proposal P1 ada di [decisions.md](decisions.md).

## 1. Konfigurasi

| ID | Isi prompt selain system prompt | Contoh | Intent | Dipakai di |
|---|---|---|---|---|
| E0-noint | smart-diff | — | tidak | RQ1 |
| E0 | smart-diff + intent | — | ya | RQ1, RQ2a, RQ3 (sekunder) |
| E2 | + 1 card terdekat dari KB campuran | 1 (label bebas) | ya | pembanding sekunder |
| E3 | + 1 card malicious terdekat | 1 M | ya | RQ2a |
| E3-k2 | + 2 card malicious terdekat | 2 M | ya | RQ2b (kontrol) |
| **E4** | + 1 malicious + 1 benign terdekat | 1 M + 1 B | ya | RQ2b, RQ3 |
| E4-noint | E4 tanpa intent | 1 M + 1 B | tidak | RQ3 |

**Invarian antar konfigurasi:**

- System prompt identik di semua konfigurasi.
- Smart-diff identik di semua konfigurasi.
- Yang boleh berbeda hanya contoh yang disertakan dan ada tidaknya blok intent.

**Urutan card E4 di-counterbalance:** urutan M→B untuk pair dengan hash `id` genap,
B→M untuk yang ganjil. Urutan ini dicatat di hasil. Alasannya, contoh terakhir
cenderung memengaruhi jawaban (recency bias).

**E1 (fixed 1-shot) dihapus.** E1 tidak menjawab gap mana pun, dan demo tetapnya
berlabel malicious sehingga efeknya tercampur dengan bias label. E1 bisa
dikembalikan sebagai pembanding sekunder kalau waktu tersisa.

### Model dan inferensi

**Model:**

- `Qwen/Qwen3-4B-Instruct-2507`
- `Qwen/Qwen2.5-Coder-3B-Instruct`

**Setelan inferensi:**

- Quantization sama untuk kedua model, dicatat.
- Server vLLM, request sekuensial.
- `max_tokens` 512.
- Anggaran konteks sama untuk kedua model.

**Tahapan run:**

| Tahap | Konfigurasi | Setelan |
|---|---|---|
| Stage 1 | 7 konfigurasi × 2 model | temperature 0, satu run |
| Stage 2 (EA2) | E0 dan E4 × 2 model | temperature 0,7, seed 0, 1, 2 |

**Volume kasar** untuk ~250 pair:

- Stage 1: 250 × 7 × 2 = 3.500 panggilan.
- Stage 2: 250 × 2 × 3 × 2 = 3.000 panggilan.
- Waktunya tergantung GPU dan panjang smart-diff.

### Format output model

```json
{"verdict": "malicious" | "benign", "evidence": ["..."], "reason": "satu kalimat"}
```

Output yang gagal di-parse diperlakukan sesuai decision rule di
[research.md §5](research.md#5-decision-rule): `benign` untuk analisis utama,
`malicious` untuk analisis sensitivitas.

## 2. Data

Satu unit data adalah satu **pair**: `pkg@v_{t−1} → pkg@v_t`.

| Subset | Definisi | Sumber | Target | Minimum |
|---|---|---|---|---|
| **MAL** | Update yang versinya tercatat *compromised*, dengan versi sebelumnya diterbitkan maintainer sah | Data Wyss et al. di OSF (46 update); entri Datadog yang manifest-nya berisi daftar versi; OSV `MAL-*`; GitHub advisory malware; dataset RogueOne (figshare) | 50 | 40 |
| **HN** | Update benign yang **menambahkan** minimal satu capability sensitif (§4), dengan tujuan sah yang terdokumentasi | Kurasi manual dari kandidat di tabel kategori | 100 (20/kategori) | 75 (15/kategori) |
| **TYP** | Update benign biasa | Sampel acak dari 2.000 typical updates Wyss et al. | 100 | 100 |

HN mendapat porsi terbesar karena FPR_HN adalah endpoint utama RQ2 dan RQ3.

**Aturan tambahan:**

- MAL berisi **maksimal 3 pair per kampanye**. Shai-Hulud, misalnya, mencakup ratusan paket dengan payload yang sama.
- 163 malicious clones milik Wyss **tidak masuk** test set utama.
- Tidak ada paket yang muncul sekaligus di test set dan di KB.
- Kalau jumlah suatu subset di bawah minimum pada Gate G1, RQ yang bergantung padanya dilaporkan deskriptif. Keputusan ini dicatat di decisions.md.

### Kategori hard negative

| # | Kategori | Contoh perilaku | Kandidat awal (sumber) |
|---|---|---|---|
| 1 | Process execution & tooling | install hook, menjalankan build/test tool | husky, patch-package, prisma (Guo et al.) |
| 2 | Telemetry | mengirim metrik penggunaan anonim | cari lewat changelog paket CLI |
| 3 | Licensing | validasi lisensi, kode lisensi yang di-obfuscate | react-native-bootsplash (Wyss et al.) |
| 4 | Network, scraper, dan unduhan | HTTP ke host eksternal, unduh biner, unggah artefak | cdk-assets, unggah ke S3 di test script (Wyss et al.) |
| 5 | Deprecation & perubahan struktur | placeholder deprecation, penghapusan file besar, ganti atau turunkan dependency | kategori FP di Tabel VI Wyss et al. |

Kandidat di atas baru nama paket. Versi yang **pertama kali menambahkan**
perilaku itu masih harus dicari.

### Kriteria label

**MAL** — kedua syarat harus terpenuhi:

- Versi tercatat compromised di minimal satu sumber: manifest Datadog, OSV `MAL-*`, GitHub advisory malware, atau Backstabber's Knife Collection.
- Versi sebelumnya diterbitkan oleh maintainer sah.

**HN** — keempat syarat harus terpenuhi:

- Tidak ada advisory untuk versi itu di OSV, GHSA, maupun Datadog.
- Diff menambahkan minimal satu capability dari §4.
- Tujuan perilakunya terdokumentasi di README, CHANGELOG, commit, atau issue.
- Penerbitnya sama dengan penerbit versi sebelumnya.

**TYP:**

- Diasumsikan benign, mengikuti asumsi Wyss et al.
- Tetap dicek sekilas bahwa tidak ada advisory.

### Proses label

1. Dua anotator melabeli seluruh MAL dan HN secara independen lewat UI audit (`frontend/`).
2. Cohen's κ dihitung dan dilaporkan.
3. Ketidaksepakatan diselesaikan lewat diskusi, dan alasannya ditulis di field `note`.
4. Pair yang tidak bisa diputuskan diberi label `skip`, dikeluarkan dari test set, dan jumlahnya dilaporkan.

### Pengambilan sampel yang aman

- **Versi benign:** unduh tarball dari URL `dist.tarball` di metadata registry, lalu ekstrak. Jangan `npm install`.
- **Versi malicious:** ambil dari arsip Datadog (zip terenkripsi, password `infected`) dan ekstrak hanya untuk dibaca.
- Tidak ada eksekusi dan tidak ada request ke endpoint yang muncul di dalam sampel.
- Simpan checksum SHA-256 setiap tarball supaya bisa direplikasi.

### Skema `data/pairs.jsonl`

| Field | Status | Isi |
|---|---|---|
| `id`, `name`, `diff` | ada | wajib |
| `before`, `after` | ada | versi v_{t−1} dan v_t |
| `intent`, `delta`, `label` | ada | intent profile (§5), capability delta (§4), label gold |
| `subset` | **baru** | `MAL` \| `HN` \| `TYP` |
| `category` | **baru** | kategori HN 1–5 |
| `campaign` | **baru** | ID kampanye; untuk benign isi dengan nama paket |
| `source` | **baru** | asal pair, misalnya `wyss-osf`, `datadog`, atau `manual` |
| `published_at` | **baru** | tanggal terbit v_t, dipakai EA3 |
| `intent_from` | **baru** | versi asal intent (harus v_{t−1}) |
| `truncated` | **baru** | apakah smart-diff dipotong |
| `gold_evidence` | **baru** | baris atau konstruksi malicious (MAL saja), dipakai EA5 |

## 3. Smart-diff

- **Generator:** pakai generator Wyss et al. dari OSF bila bisa diakses (minify → unminify, lalu eliminasi kode redundan). Kalau tidak bisa, reimplementasikan dan catat perbedaannya.
- **Wajib menyertakan diff `package.json`:** dependencies, scripts, dan sumber dependency (registry vs git/URL). Payload axios 2026 dan kategori "Trigger Dependency" di Wyss masuk lewat dependency, bukan lewat kode JS.
- **Anggaran konteks** ditetapkan di M3 berdasarkan distribusi panjang smart-diff, sama untuk kedua model, dan dicatat di decisions.md.
- **Pemotongan:** kalau smart-diff melebihi anggaran, file terbesar dipotong lebih dulu, lalu pair diberi `truncated=true`.

## 4. Capability delta

**Aturan dasar:**

- Delta diekstrak **otomatis** oleh extractor rule-based yang sama untuk pair dan card.
- Delta tidak boleh dilabeli manual, karena itu memasukkan penilaian manusia ke input model.
- Delta berisi capability yang muncul di v_t tetapi tidak ada di v_{t−1}.

| Capability | Contoh sinyal |
|---|---|
| `network` | `http`, `https`, `net`, `dgram`, `fetch`, klien HTTP |
| `process_exec` | `child_process` (`exec`, `spawn`, `execSync`) |
| `env_access` | `process.env`, `os.userInfo`, `os.homedir` |
| `fs_sensitive` | akses ke `~/.ssh`, `~/.npmrc`, `.env`, dan file kredensial lain |
| `install_script` | `preinstall`/`install`/`postinstall` baru atau berubah |
| `dynamic_code` | `eval`, `new Function`, `vm.runIn*` |
| `obfuscation` | string ter-encode panjang, decode lalu eksekusi |
| `dependency_change` | dependency baru, diganti, atau bersumber non-registry |
| `large_deletion` | penghapusan sebagian besar file (ambang ditetapkan di M3) |

Daftar ini dibekukan di akhir M3. Perubahan setelah itu berarti semua
konfigurasi dijalankan ulang.

## 5. Intent profile

- **Sumber:** versi sebelumnya (v_{t−1}), berupa `description`, `keywords`, bagian awal README yang dipotong ke anggaran tetap, dan daftar `scripts`.
- **Kenapa v_{t−1}:** pada update yang dikompromikan, penyerang mengendalikan v_t, termasuk README-nya.
- **Konfigurasi `*-noint`:** blok intent dihapus seluruhnya, sementara system prompt tidak berubah.

## 6. Knowledge base dan retrieval

**Isi KB:**

- **Card malicious:** dari paket Datadog berkategori *malicious intent*, misalnya typosquat. Paket seperti ini tidak bisa jadi pair karena tidak punya versi benign sebelumnya, tetapi perilakunya sah dipakai sebagai contoh. Target sekitar 50 card.
- **Card benign:** dari pool hard negative yang terpisah dari test set, minimal 5 per kategori. Target 25–50 card.

**Skema card:** `id`, `label`, `name`, `intent`, `delta`, `summary` (1–2 kalimat
alasan), `campaign`, `source`.

**Retrieval:**

- Skor dihitung dengan Jaccard pada capability delta, sesuai yang sudah ada di runner.
- **Card dengan paket atau kampanye yang sama dengan pair dikecualikan.**
- Kalau skor seri, card dipilih berdasarkan urutan di KB.

**Log:** setiap run menyimpan ID card, label, dan skor. Log ini dipakai untuk
EA4 (retrieval error) dan untuk memeriksa apakah card benign rata-rata kurang
mirip dibanding card malicious.

**Dev set:** maksimal 10 pair dari pool KB, hanya untuk smoke test prompt.
Prompt tidak pernah disetel pada test set.

## 7. Metrik dan analisis

| Jenis | Metrik |
|---|---|
| Primer | FPR_HN dan Recall, dengan Wilson 95% CI |
| Sekunder | FPR_TYP, precision, F1 (dengan rasio kelas dicatat), JSON validity rate, token input/output, median dan p95 latency, peak VRAM |
| Dihapus | PR-AUC — verdict biner tidak menghasilkan skor |

Prosedur uji dan label hasil ada di [research.md §5](research.md#5-decision-rule).

### Batas yang bisa dibuktikan

Lebar Wilson 95% CI untuk satu proporsi:

| n | Proporsi | CI | Lebar |
|---|---|---|---|
| 50 (MAL) | recall 0,9 | [0,786; 0,957] | ±8,5 poin |
| 50 (MAL) | recall 0,8 | [0,670; 0,888] | ±10,9 poin |
| 100 (HN) | FPR 0,2 | [0,133; 0,289] | ±7,8 poin |
| 100 (HN) | FPR 0,1 | [0,055; 0,174] | ±6,0 poin |

McNemar exact dua sisi: jumlah maksimum pair yang berubah ke arah sebaliknya
agar hasilnya signifikan, dari *d* pair yang verdict-nya berbeda antara dua
konfigurasi.

| d | α = 0,05 | α = 0,0083 (langkah pertama Holm, 6 uji) |
|---|---|---|
| 15 | ≤ 3 | ≤ 2 |
| 20 | ≤ 5 | ≤ 3 |
| 25 | ≤ 7 | ≤ 5 |
| 30 | ≤ 9 | ≤ 7 |

**Artinya:**

- Batas "recall tidak turun lebih dari 5 poin" **tidak bisa dibuktikan** dengan MAL sekitar 50. Batas ini dilaporkan sebagai estimasi titik ditambah CI, sesuai label "Didukung sebagian".
- Penurunan FPR_HN di bawah sekitar 15 poin kemungkinan besar tidak terdeteksi, kecuali hampir tidak ada pair yang berubah ke arah sebaliknya.
- Kondisi di atas adalah batas desain, bukan bukti bahwa efeknya tidak ada.

## 8. Timeline dan gate

| Minggu | Pekerjaan | Keluaran | Gate |
|---|---|---|---|
| M1–2 | Kumpulkan MAL/HN/TYP; tulis kriteria label; label ganda; hitung κ; susun daftar capability awal | `data/pairs.jsonl` berlabel, nilai κ | **G1:** jumlah per subset dibandingkan dengan minimum untuk menentukan RQ mana yang diuji inferensial. Catat di decisions.md |
| M3–4 | Smart-diff, intent profile, capability extractor, KB, retrieval dengan pengecualian, konfigurasi revisi, skrip analisis (diuji dengan data dummy) | smoke test `--limit 5` untuk semua konfigurasi | **G2:** bekukan prompt, konfigurasi, daftar capability, anggaran konteks, dan decision rule |
| M5–6 | Stage 1, Stage 2, pencatatan VRAM | `data/results.jsonl` | — |
| M7–8 | Analisis sesuai decision rule; EA1–EA5 (error analysis di UI audit); penulisan | tabel dan naskah | — |

## 9. Checklist implementasi

Status per 2026-09-13. Kode saat ini masih mengikuti desain E0–E4 lama.

**Prompt** — [pipeline/prompts.py](../pipeline/prompts.py)

- [ ] Ganti `CONFIGS` menjadi `E0-noint, E0, E2, E3, E3-k2, E4, E4-noint` dan hapus `E1` ([L8](../pipeline/prompts.py#L8)).
- [ ] Hapus daftar "telemetry opt-in, tooling test, perubahan lisensi, scraper, deprecation" dari `SYSTEM` ([L14-L15](../pipeline/prompts.py#L14-L15)), karena daftar itu sama persis dengan kategori HN (D17). Ubah frasa "kesesuaian dengan intent paket" ([L13](../pipeline/prompts.py#L13)) menjadi "…bila disertakan" supaya system prompt tetap identik untuk `*-noint`.
- [ ] Untuk `*-noint`, hilangkan baris intent sepenuhnya ([L34](../pipeline/prompts.py#L34)).

**Runner** — [pipeline/runner.py](../pipeline/runner.py)

- [ ] Perbarui `retrieve` ([L54-L66](../pipeline/runner.py#L54-L66)):
  - kecualikan card dengan `name` atau `campaign` yang sama dengan pair;
  - `E3-k2` mengambil 2 card malicious;
  - `E4` memakai urutan counterbalance (sekarang selalu M→B di [L66](../pipeline/runner.py#L66)).
- [ ] Simpan `cards` (ID, label, skor) dan urutannya di setiap baris hasil.
- [ ] Tambah flag `--temperature` untuk EA2; sekarang nilainya tetap 0 di [L84](../pipeline/runner.py#L84).
- [ ] Default `--base-url` port 8000 ([L107](../pipeline/runner.py#L107)) bentrok dengan backend. Ganti default atau dokumentasikan.

**Komponen baru**

- [ ] Smart-diff generator, termasuk diff `package.json` (§3).
- [ ] Intent profile builder dari v_{t−1} (§5).
- [ ] Capability extractor (§4), dipakai untuk pair dan card.
- [ ] Skrip analisis: Wilson CI, McNemar exact, Holm, bootstrap per kampanye, kebijakan output tidak valid, dan Pareto front.

**Data dan UI**

- [ ] Tambah field baru pada skema pair (§2). Tipe `Pair` di [frontend/src/types/api.ts](../frontend/src/types/api.ts#L10-L20) belum memuatnya; filter per `subset` dan `category` akan membantu audit.
- [ ] Dukung label ganda. Backend menyimpan satu keputusan per pair di `data/audit_decisions.json`, jadi perlu file per anotator atau field `annotator` untuk menghitung κ.
- [x] Taksonomi error capability/intent/retrieval sudah ada di UI dan sesuai dengan EA4.
