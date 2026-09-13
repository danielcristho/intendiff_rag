# Posisi terhadap RogueOne

**Sumber:** Sofaer, David, Kang, Yu, Cao, Yang, Nieh. *RogueOne: Detecting Rogue
Updates via Differential Data-flow Analysis Using Trust Domains.* ICSE 2024.
DOI 10.1145/3597503.3639199. Repo: https://github.com/columbia/rogueone.

Isi file ini dibaca langsung dari PDF paper pada 2026-09-13. Keputusan terkait
RogueOne ada di `docs/decisions.md` (D18, D20).

## RogueOne secara singkat

- **Cara kerja:** RogueOne membandingkan versi lama dan versi baru sebuah paket. Update ditandai rogue kalau muncul **aliran data baru antar trust domain**.
- **Trust domain:** objek dikelompokkan berdasarkan asalnya, yaitu paket itu sendiri, tiap dependency, atau API sistem. Asumsinya, objek dari paket yang sama dikendalikan developer yang sama.
- **Pelacakan aliran data:** lewat Object Data-flow Relationship Graph (ODRG) yang dibangun dengan abstract interpretation (berbasis ODGen dan FAST).
- **Tanpa deny-list:** pendekatan ini tidak memakai daftar API mencurigakan.

**Threat model-nya sama dengan penelitian ini:** update jahat pada paket benign
yang sudah ada ("Inject into Source" dan "Inject into Repository System" dalam
taksonomi Ohm et al.). Paket yang jahat sejak awal, seperti typosquat, berada di
luar scope. Karena itu typosquat di penelitian ini hanya dipakai sebagai card KB,
bukan sebagai pair (D13).

## Angka yang boleh dikutip

**Dataset**

- Multi-version: 333 update dari 12 paket (7 rogue).
- Single-update: 341 update, terdiri dari 300 benign (update terbaru paket populer dan acak), 29 rogue dari Backstabber's Knife Collection, dan 12 rogue lain.

**Hasil deteksi**

| Konfigurasi | Dataset | Rogue terdeteksi | False positive |
|---|---|---|---|
| RogueOne (default) | Single-update | 31/41 (75,6%) | 14/300 (4,7%) |
| RogueOne-Paranoid | Single-update | 38/41 (92,7%) | 120/300 (40,0%) |
| RogueOne (default) | Multi-version | 7/7 | 17/326 (5,2%) |

Per jenis serangan pada gabungan kedua dataset (48 rogue), tingkat deteksinya
79% untuk default dan 94% untuk Paranoid.

**Waktu analisis**

- 5 update kena timeout 1 jam.
- Sisanya rata-rata 226,7 detik per update; 90% selesai dalam kurang dari 4 detik, 95% dalam kurang dari 30 menit.
- Error dan timeout dihitung sebagai benign.

## Ide yang diambil

| Ide RogueOne | Bentuknya di IntentDiff-RAG | Status |
|---|---|---|
| Analisis diferensial: menilai perubahan antar versi, bukan paket utuh | Smart-diff dan capability delta (v_t dikurangi v_{t−1}) | Diambil |
| Trust domain: yang mencurigakan adalah interaksi baru dengan pihak di luar paket | Capability delta sebagai versi kasarnya: capability yang baru muncul (network, exec, fs, dependency) | Diambil sebagai konsep, tanpa data-flow |
| Dependency baru sebagai sinyal (kasus event-stream / flatmap-stream) | Diff `package.json` wajib ada, plus capability `dependency_change` | Diambil (D15) |
| Dataset single-update: update terbaru paket populer + acak sebagai benign, insiden publik sebagai rogue | Lewat Wyss et al., yang memperluas metodologi ini; subset TYP diambil dari data Wyss | Diambil |
| Error dan timeout dihitung benign | Output invalid dihitung benign, dengan analisis sensitivitas | Diambil (D18) |
| Trade-off sensitivitas antara default dan Paranoid | Argumen untuk fokus pada FPR, dan dasar label "Didukung sebagian" pada batas recall | Diambil sebagai argumen |

## Ide yang di-skip

| Ide RogueOne | Alasan di-skip |
|---|---|
| ODRG dengan abstract interpretation (ODGen/FAST) | Berat dan rawan timeout. RQ penelitian ini tentang LLM, bukan analisis data-flow |
| Analisis rekursif dependency transitif | Butuh kode dependency dan waktu analisis; di luar scope 8 minggu |
| Trust domain granular per nilai (Paranoid) | Tidak ada padanannya di level teks, dan FP-nya 40% pada dataset single-update |
| Menjalankan RogueOne sebagai baseline di data kita | D20: rata-rata 226,7 detik per update, timeout 1 jam, butuh setup ODGen. Membandingkan dengan angka paper juga tidak sah karena datanya berbeda |

## Pelajaran yang memengaruhi desain

- **Serangan tersamar (CC-Harvest).** Kalau payload memakai API yang sudah dipakai versi sebelumnya, RogueOne default melewatkan 10 dari 10 kasus karena tidak ada aliran data baru. Capability delta punya titik buta yang sama: delta bisa kosong. Karena itu recall untuk pair MAL dengan delta kosong dilaporkan terpisah. Pada pair seperti ini retrieval juga tidak punya sinyal, karena semua card berskor 0.
- **Sumber false positive RogueOne mirip kategori HN kita.** Tabel 4 (hitungan konfigurasi Paranoid pada kedua dataset): dependency baru 41 kasus, install script 14, API sistem baru 8. Ini mendukung kategori HN 1 (tooling/install script), 4 (network), dan 5 (perubahan dependency).
- **Obfuscation.** Minification tidak memengaruhi RogueOne, tetapi teknik seperti global array menyebabkan over-approximation. Ketahanan terhadap obfuscation berada di luar scope penelitian ini.
- **Review false positive** biasanya tidak lebih dari dua menit per kasus lewat UI sederhana. Perannya sama dengan UI audit kita untuk error analysis (EA4).

## Cara menulis RogueOne di naskah

- **Letakkan di related work** sebagai pendekatan non-LLM yang paling dekat untuk rogue update. Pendekatannya kuat, tetapi mahal secara komputasi dan harus menukar recall dengan false positive (default vs Paranoid).
- **Jangan menulis bahwa IntentDiff-RAG lebih baik atau lebih murah** berdasarkan angka paper, karena datanya berbeda.
- **Yang boleh:** menjelaskan perbedaan jenis biaya secara kualitatif (abstract interpretation per update vs satu inferensi LLM per konfigurasi), lalu menyajikan latency kita sendiri dari RQ4.
