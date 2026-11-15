# Hasil ablasi temperature × seed — D111, 12 November 2026

Protokol: [sampling-ablation-20261109.md](sampling-ablation-20261109.md).
Data dan keluaran ada di `data/evaluation/sampling-ablation-20261109/`
(`metrics.csv`, `stability.csv`, `contrasts.csv`, `summary.json`). Laporan
dibuat dengan perintah berikut dari root repo:

```
python pipeline/sampling_report.py --release data/evaluation/sampling-ablation-20261109
```

Grafik ada di `data/evaluation/sampling-ablation-20261109/figures/` (PDF dan PNG
300 dpi), dibuat dengan `python pipeline/sampling_plots.py --release
data/evaluation/sampling-ablation-20261109`:

| File | Isi | Bagian |
|---|---|---|
| `sampling-rates` | TPR dan FPR per konfigurasi terhadap temperature, dengan rentang antar seed. Skala y sama per baris | §3 |
| `sampling-flips` | Flip rate antar seed terhadap temperature, untuk seluruh pair dan untuk MAL | §4 |
| `sampling-contrasts` | ΔTPR dan ΔFPR ketiga kontras per seed dan temperature, dengan CI 95% | §5 |

Grid lengkap: 24 sel (2 model × 4 temperature × 3 seed), masing-masing 11.982
respons, total **287.568 respons**, tanpa error transport. Seluruh sel lolos
`source_results.verify`. Ablasi ini deskriptif. Tabel utama naskah tetap memakai
T=0, seed 0, dan tidak ada setelan decoding yang dipilih dari grid ini.

| Keluaran | SHA-256 |
|---|---|
| `metrics.csv` | `cc408e785b3ea778da1ea396d738c89cd724e3e82fe118643146a634f3ddd4be` |
| `stability.csv` | `06c34aae0ada2b0b73b81b3f208777f9bdc75fac09667215cae1700965d2055b` |
| `contrasts.csv` | `8cbd8d16ff070ce4064cf09f796cebfe9f5591bd652ff316b1585f9d3dd86967` |
| `summary.json` | `3562d02871457d7d141835f1b27a37aa1111be7a21e98a450966beb0e3148c74` |

## 1. Reproduksi sel referensi

Sel (T=0, seed 0) dijalankan ulang di lingkungan yang dipasang ulang, lalu
dibandingkan per pair dengan run historis D101/D105.

| Model | Verdict sama | Teks mentah identik |
|---|---:|---:|
| Qwen3-4B | 11.982 / 11.982 | 11.976 / 11.982 |
| Qwen2.5-Coder-3B | 11.979 / 11.982 | 11.963 / 11.982 |

Ketiga verdict Qwen2.5-Coder yang berbeda ada di DIFF+I+MM (1) dan DIFF+I+MB (2).
Angka T=0 di naskah terreproduksi. Sisa perbedaannya konsisten dengan
nondeterminisme numerik antar build (D54).

Sel referensi, dengan CI bootstrap kampanye 95%:

| Model | Konfigurasi | TPR | FPR | Invalid |
|---|---|---|---|---:|
| Qwen3-4B | DIFF | 0,481 [0,385–0,577] | 0,064 [0,053–0,075] | 150 |
| | DIFF+I | 0,450 [0,352–0,548] | 0,041 [0,032–0,050] | 92 |
| | DIFF+I+M | 0,457 [0,359–0,555] | 0,048 [0,039–0,058] | 71 |
| | DIFF+I+MM | 0,419 [0,327–0,508] | 0,033 [0,025–0,041] | 61 |
| | DIFF+I+MB | 0,504 [0,409–0,600] | 0,056 [0,046–0,066] | 61 |
| | DIFF+MB | 0,512 [0,416–0,607] | 0,079 [0,067–0,092] | 89 |
| Qwen2.5-Coder-3B | DIFF | 0,760 [0,680–0,832] | 0,596 [0,574–0,619] | 20 |
| | DIFF+I | 0,829 [0,764–0,889] | 0,593 [0,571–0,615] | 18 |
| | DIFF+I+M | 0,783 [0,711–0,851] | 0,486 [0,463–0,508] | 1 |
| | DIFF+I+MM | 0,798 [0,722–0,865] | 0,482 [0,460–0,505] | 4 |
| | DIFF+I+MB | 0,853 [0,787–0,911] | 0,565 [0,543–0,588] | 9 |
| | DIFF+MB | 0,783 [0,705–0,855] | 0,543 [0,521–0,566] | 4 |

## 2. Seed pada T=0

- **Qwen3-4B:** flip rate 0 di keenam konfigurasi. Ketiga seed memberi verdict
  yang sama untuk setiap pair.
- **Qwen2.5-Coder-3B:** flip rate paling tinggi 0,05%, yaitu satu pair TYP per
  konfigurasi. Tidak ada flip pada MAL, dan TPR identik di ketiga seed.

Seed tidak berpengaruh pada decoding greedy. Perbedaan kecil pada Qwen2.5-Coder
berasal dari nondeterminisme numerik server, bukan dari seed.

## 3. Pengaruh temperature

Nilai berikut adalah rerata tiga seed, ditulis sebagai TPR / FPR.

| Model | Konfigurasi | T=0 | T=0,3 | T=0,7 | T=1,0 |
|---|---|---|---|---|---|
| Qwen3-4B | DIFF | 0,481 / 0,064 | 0,470 / 0,062 | 0,465 / 0,063 | 0,457 / 0,065 |
| | DIFF+I | 0,450 / 0,041 | 0,437 / 0,048 | 0,450 / 0,047 | 0,460 / 0,045 |
| | DIFF+I+M | 0,457 / 0,048 | 0,437 / 0,047 | 0,447 / 0,045 | 0,468 / 0,044 |
| | DIFF+I+MM | 0,419 / 0,033 | 0,437 / 0,032 | 0,421 / 0,034 | 0,434 / 0,036 |
| | DIFF+I+MB | 0,504 / 0,056 | 0,486 / 0,055 | 0,509 / 0,053 | 0,504 / 0,050 |
| | DIFF+MB | 0,512 / 0,079 | 0,519 / 0,079 | 0,512 / 0,082 | 0,509 / 0,081 |
| Qwen2.5-Coder-3B | DIFF | 0,760 / 0,596 | 0,729 / 0,560 | 0,705 / 0,496 | 0,654 / 0,466 |
| | DIFF+I | 0,829 / 0,593 | 0,793 / 0,549 | 0,718 / 0,463 | 0,698 / 0,450 |
| | DIFF+I+M | 0,783 / 0,486 | 0,762 / 0,443 | 0,700 / 0,382 | 0,661 / 0,366 |
| | DIFF+I+MM | 0,798 / 0,482 | 0,739 / 0,441 | 0,708 / 0,388 | 0,643 / 0,374 |
| | DIFF+I+MB | 0,853 / 0,565 | 0,837 / 0,534 | 0,801 / 0,466 | 0,734 / 0,445 |
| | DIFF+MB | 0,783 / 0,544 | 0,780 / 0,531 | 0,747 / 0,460 | 0,682 / 0,435 |

- **Qwen3-4B** praktis tidak terpengaruh temperature. Rerata TPR bergeser paling
  jauh 2,3 poin (DIFF), dan FPR 0,7 poin. Semua pergeseran itu berada di dalam CI
  kampanye sel referensi.
- **Qwen2.5-Coder-3B** bergeser searah di keenam konfigurasi: TPR dan FPR
  sama-sama turun seiring naiknya temperature. Dari T=0 ke T=1,0, TPR turun 10–16
  poin dan FPR turun 11–14 poin. Sampling menggeser keputusan ke arah benign, dan
  pada model ini, yang pada T=0 menandai 48–60% TYP sebagai malicious, efeknya
  menurunkan kedua laju sekaligus.

## 4. Stabilitas antar seed

Flip rate adalah proporsi pair yang verdict-nya tidak sama di ketiga seed. Tabel
berikut memberi rentangnya di keenam konfigurasi.

| Model | T | Flip seluruh pair | Flip MAL |
|---|---|---|---|
| Qwen3-4B | 0 | 0 | 0 |
| | 0,3 | 3,1–4,8% | 6,2–12,4% |
| | 0,7 | 4,3–7,4% | 13,2–16,3% |
| | 1,0 | 4,9–8,7% | 13,2–17,8% |
| Qwen2.5-Coder-3B | 0 | 0–0,05% | 0 |
| | 0,3 | 28,7–36,4% | 12,4–23,3% |
| | 0,7 | 41,6–49,2% | 23,3–38,0% |
| | 1,0 | 50,1–58,5% | 27,1–48,1% |

Pada Qwen2.5-Coder, T=0,3 saja sudah membuat sekitar sepertiga pair berganti
verdict antar seed, dan pada T=1,0 lebih dari separuh pair. Banyak keputusan
greedy model ini ternyata hanya berselisih tipis antara benign dan malicious.
Qwen3-4B jauh lebih stabil. Pada Qwen3-4B, flip lebih sering terjadi pada MAL
daripada TYP. Pada Qwen2.5-Coder sebaliknya, flip lebih sering terjadi pada TYP.

Rentang TPR antar seed pada satu sel paling lebar 5,4 poin untuk Qwen3-4B
(DIFF+I+M, T=0,7) dan 10,1 poin untuk Qwen2.5-Coder (DIFF+I, T=0,7). Dengan
129 MAL, satu pair setara 0,78 poin TPR.

## 5. Ketahanan kontras

ΔTPR dan ΔFPR berpasangan dihitung di setiap sel (12 per model). "Searah" berarti
tandanya sama dengan sel referensi. "CI ≠ 0" berarti CI 95% tidak mencakup nol.

| Model | Kontras | ΔTPR searah | ΔTPR CI ≠ 0 | ΔFPR searah | ΔFPR CI ≠ 0 | Rentang ΔTPR | Rentang ΔFPR |
|---|---|---:|---:|---:|---:|---|---|
| Qwen3-4B | DIFF+I → DIFF+I+M | 7 | 0 | 6 | 0 | −3,1 s.d. +3,1 | −0,7 s.d. +0,7 |
| | DIFF+I+MM → DIFF+I+MB | 12 | 8 | 12 | 11 | +3,9 s.d. +10,1 | +1,0 s.d. +2,7 |
| | DIFF+MB → DIFF+I+MB | 9 | 0 | 12 | 12 | −5,4 s.d. +0,8 | −3,6 s.d. −2,2 |
| Qwen2.5-Coder-3B | DIFF+I → DIFF+I+M | 10 | 1 | 12 | 12 | −9,3 s.d. +4,7 | −11,7 s.d. −7,0 |
| | DIFF+I+MM → DIFF+I+MB | 12 | 6 | 12 | 12 | +3,1 s.d. +12,4 | +6,6 s.d. +10,2 |
| | DIFF+MB → DIFF+I+MB | 12 | 4 | 10 | 1 | +0,8 s.d. +9,3 | −1,2 s.d. +3,2 |

- Efek yang jelas pada T=0 tetap searah di **semua** sel:
  - MM → MB menaikkan TPR dan FPR pada kedua model.
  - Intent (DIFF+MB → DIFF+I+MB) menurunkan FPR Qwen3-4B. CI-nya tidak pernah
    mencakup nol.
  - Contoh rujukan (DIFF+I → DIFF+I+M) menurunkan FPR Qwen2.5-Coder. CI-nya juga
    tidak pernah mencakup nol.
- Kontras yang pada T=0 sudah tidak terbedakan dari nol berganti tanda antar sel,
  misalnya ΔTPR DIFF+I → DIFF+I+M dan ΔTPR intent pada Qwen3-4B. Ini sesuai
  dengan efek yang memang tidak terukur, bukan temuan baru.
- ΔTPR MM → MB signifikan pada 8 dari 12 sel Qwen3-4B dan 6 dari 12 sel
  Qwen2.5-Coder. Arahnya stabil, tetapi besarnya pada n=129 MAL bergantung pada
  sampel decoding.

## 6. Format, biaya, dan sensitivitas invalid

| Model | T | Validitas JSON (min–maks) | Rerata token keluaran | Median latensi |
|---|---|---|---:|---:|
| Qwen3-4B | 0 | 0,925–0,969 | 59,1 | 338 ms |
| | 1,0 | 0,902–0,973 | 58,1 | 341 ms |
| Qwen2.5-Coder-3B | 0 | 0,990–0,999 | 67,8 | 477 ms |
| | 1,0 | 0,981–0,994 | 71,8 | 477 ms |

Temperature hampir tidak mengubah validitas JSON, karena constrained decoding
xgrammar tetap membatasi bentuk keluaran. Biaya per request juga tidak berubah.
Dengan invalid dihitung sebagai malicious, TPR Qwen3-4B naik paling banyak
11,6 poin dan FPR-nya 9,6 poin. Pada Qwen2.5-Coder kenaikannya 6,2 dan 1,8 poin.
Pola ini sama dengan T=0, karena invalid Qwen3-4B memang lebih banyak.

## 7. Implikasi untuk naskah

- Keterbatasan "satu run, satu seed" bisa dipersempit. Pada T=0, verdict tidak
  bergantung pada seed, dan angka naskah terreproduksi di lingkungan yang
  dipasang ulang.
- Kesimpulan arah ketiga kontras yang dilaporkan sebagai efek pada T=0 bertahan
  di T hingga 1,0. Kontras yang dilaporkan sebagai tidak terbedakan dari nol
  tetap tidak terbedakan.
- Qwen2.5-Coder-3B sangat sensitif terhadap sampling. Tingkat operasinya pada T=0
  (TPR dan FPR tinggi) adalah sifat decoding greedy, bukan keputusan yang mantap
  per pair. Ini relevan untuk pembahasan kalibrasi model kecil.
- Klaim ketahanan decoding hanya berlaku untuk dua model ini. Kelima model D102
  hanya punya hasil T=0.

## 8. Penyimpangan eksekusi

Rinciannya ada di `data/evaluation/sampling-ablation-20261109/recovery/README.md`.

- **Karakter U+2028/U+0085 di jawaban model.** Ketiga sel Qwen2.5-Coder T=1,0
  memuat karakter ini, sehingga `load_jsonl` (`str.splitlines`) memotong baris.
  File hasil ditulis ulang dengan escape ASCII. Isinya identik per baris setelah
  `json.loads`, dan file aslinya disimpan di `recovery/`. Kode runner yang di-pin
  tidak diubah.
- **Restart server.** Server Qwen2.5-Coder dinyalakan ulang dua kali: setelah
  gangguan memori GPU di WSL, dan setelah Windows me-restart sendiri untuk update
  KB5132061 pada 12 November pukul 00.00, yang memotong sel T=1,0 seed 1 di
  respons ke-3.206. Seed dikirim per request, jadi sampel tidak bergantung pada
  sesi server. Runner melanjutkan tanpa mengulang respons yang sudah ada.
- **Batas GPU di WSL2.** Satu proses hanya bisa mengalokasikan GPU kira-kira
  sebesar RAM bebas Windows dikurangi ±4,5 GiB. Page cache WSL ikut memakan RAM
  itu. `recovery/evict_cache.py` melepas page cache bobot dan file release
  selama batch berjalan, tanpa menyentuh request, flag, maupun hasil.
