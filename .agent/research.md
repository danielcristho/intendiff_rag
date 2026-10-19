# Ringkasan penelitian untuk agent

Sumber kebenaran: [docs/research.md](../docs/research.md) untuk RQ dan [docs/methodology.md](../docs/methodology.md) untuk prosedur. File ini adalah
ringkasan operasional supaya agent tidak melanggar desain saat mengubah kode
atau menulis teks. Kalau isinya berbeda dengan `docs/`, yang benar `docs/`,
dan file ini yang harus diperbarui.

## Pertanyaan inti

Bisakah LLM open-weight 3–4B membedakan update npm berbahaya dari update sah
yang perilakunya mirip? Apakah contoh benign pembanding dan intent paket menekan
false positive-nya?

## RQ, konfigurasi, dan endpoint

| RQ | Dibandingkan | Endpoint | Cara menjawab |
|---|---|---|---|
| RQ1 | DIFF, DIFF+I | Recall, FPR_TYP, FPR_HN dengan Wilson CI | deskriptif |
| RQ2a | DIFF+I+M vs DIFF+I | FPR_HN | McNemar exact + Holm |
| **RQ2b (utama)** | DIFF+I+MB vs DIFF+I+MM | FPR_HN, batas recall −5 poin | McNemar exact + Holm; bootstrap recall per kampanye |
| RQ3 | DIFF+I+MB vs DIFF+MB | FPR_HN, batas recall −5 poin | sama dengan RQ2b |
| RQ4 | semua konfigurasi | token, latency median/p95, memori GPU terhitung | deskriptif |

Hanya ada **6 uji konfirmatori**: H2a, H2b, dan H3 untuk masing-masing dari 2 model.
Semua analisis lain bersifat eksploratif (EA1–EA5). Label hasil ("Didukung",
"Didukung sebagian", dan seterusnya) ada di `docs/research.md` §5.

## Invarian yang tidak boleh dilanggar

| Invarian | Akibat kalau dilanggar |
|---|---|
| System prompt dan smart-diff identik di semua konfigurasi | Semua perbandingan batal |
| DIFF+I+MM dan DIFF+I+MB sama-sama berisi 2 card | RQ2b tidak bisa memisahkan efek contrastive dari efek jumlah contoh |
| `DIFF+MB` hanya menghapus blok intent dari `DIFF+I+MB` | RQ3 batal |
| Intent diambil dari v_{t−1} | Penyerang bisa memengaruhi intent lewat README di v_t |
| Retrieval mengecualikan card dari paket atau kampanye yang sama dengan pair | Terjadi kebocoran; RQ2 dan RQ3 batal |
| Urutan card DIFF+I+MM dan DIFF+I+MB di-counterbalance dengan aturan yang sama (card malicious teratas di posisi yang sama) | RQ2b tercampur recency bias |
| Retrieval tidak membaca intent | DIFF+I+MB dan DIFF+MB mendapat card berbeda; RQ3 batal |
| Nama paket dan capability delta tidak pernah masuk prompt | RQ1 mengukur extractor atau hafalan model, bukan kemampuan membaca smart-diff (D25, D26) |
| Smart-diff dipotong sekali per pair dengan tokenizer Qwen2.5-Coder-3B dan dipakai apa adanya oleh semua konfigurasi dan kedua model | Input berbeda antar konfigurasi atau antar model |
| Teks prompt disalin verbatim dari methodology §6 | Prompt yang diuji tidak sama dengan yang dilaporkan |
| Capability delta diekstrak otomatis dengan extractor yang sama untuk pair dan card | Penilaian manusia bocor ke input model |
| Stage 1 memakai temperature 0 dan request sekuensial | Hasil tidak reproducible; latency RQ4 rusak |
| Runner menyimpan output mentah; kebijakan output invalid diterapkan di skrip analisis | Analisis sensitivitas D18 tidak bisa dijalankan |
| Prompt tidak menyebut kategori hard negative | FPR_HN terlalu optimis (D17) |

## Jangan

- Jangan menyetel prompt, konfigurasi, atau daftar capability setelah melihat hasil test set. Setelah Gate G2, setiap perubahan wajib dicatat di `docs/decisions.md` dan semua konfigurasi dijalankan ulang.
- Jangan menulis bahwa metode ini "lebih baik" dari RogueOne, IntelGuard, atau Wyss et al. Data dan setup-nya berbeda, jadi angka mereka hanya konteks di Diskusi (D23).
- Jangan menulis "tidak ada efek" dari hasil yang tidak signifikan. Tulis batas deteksi desainnya.
- Jangan menambah uji konfirmatori tanpa memperbarui koreksi Holm dan `docs/decisions.md`.
- Jangan mengklaim intent mismatch sebagai ide baru; yang baru adalah pengukurannya (D3). Klaim kebaruan utama ada di Gap 2.
- Jangan menjalankan, meng-install, atau mengakses endpoint dari sampel malicious.

## Istilah

| Istilah | Arti |
|---|---|
| pair | satu update `pkg@v_{t−1} → pkg@v_t` |
| MAL / HN / TYP | subset update malicious / hard negative / typical |
| hard negative | update benign yang menambahkan capability sensitif dengan tujuan sah yang terdokumentasi |
| capability delta | capability yang ada di v_t tetapi tidak ada di v_{t−1} |
| intent profile | `description`, `keywords`, bagian awal README, dan `scripts` dari v_{t−1} |
| card | contoh di KB berlabel malicious atau benign, berisi intent, delta, dan ringkasan alasan |
| kampanye | kelompok pair dengan pelaku atau payload yang sama (misalnya Shai-Hulud); menjadi unit bootstrap dan unit pengecualian retrieval |
| FPR_HN | proporsi pair HN yang diberi verdict `malicious` |

## Saat menulis naskah

- Referensi utama: Wyss et al. (RAID 2025). Fakta yang boleh dikutip dan koreksi slide P1 ada di `docs/references.md`.
- Contoh motivasi: chalk/debug, Shai-Hulud, dan axios. CVE-2025-66478 bukan contoh update berbahaya.
- Posisi penelitian: triage update dependensi sebelum advisory terbit, bukan audit tata kelola TI.
- Posisi terhadap RogueOne ada di [rogueone.md](rogueone.md).
