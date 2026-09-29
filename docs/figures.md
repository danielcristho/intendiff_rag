# Cara membaca figur dan tabel hasil

Dihasilkan oleh `python -m pipeline plots` (PDF + PNG) dan `python -m pipeline tables` (workbook),
keduanya membaca angka yang sama dari `pipeline/results/report.py`. Kalau figur dan sheet
berbeda, salah satunya tidak di-regenerate — jalankan ulang keduanya.

```
make venv
.venv/bin/python -m pipeline plots
.venv/bin/python -m pipeline tables
```

## Aturan yang berlaku untuk semua figur

- **Abu-abu Qwen2.5-Coder-3B, biru Qwen3-4B**, kecuali di Figure 2 baris atas, di mana
  abu-abu berarti baseline dan biru berarti variant.
- **Batang dan titik adalah estimasi titik; whisker adalah intervalnya.** Yang boleh
  diklaim adalah intervalnya, bukan batangnya.
- **Interval tumpang tindih berarti selisihnya belum terbukti**, berapa pun jarak
  ujung batangnya.
- **Bandingkan di dalam satu panel, bukan antar panel.** Panel berbeda punya
  denominator berbeda (MAL, HN, TYP).
- **Batang setinggi nol tetap digambar sebagai garis di y = 0.** Panel yang tampak
  kosong berarti 0%, bukan data hilang. Whisker-nya diwarnai mengikuti modelnya,
  jadi batang nol tetap bisa dikenali miliknya siapa.
- Nilai *p* tidak pernah ada di gambar. Semuanya di sheet **comparisons**, kolom
  `p (Holm)`.

## Figure 1 — `fig_rates`

Tiga panel, sumbu-y persen, sumbu-x konfigurasi.

| Panel | Metrik | Arah yang baik | Denominator |
|---|---|---|---|
| (a) | Recall on MAL | tinggi | pair MAL |
| (b) | FPR on hard negatives | **rendah** | pair HN |
| (c) | FPR on typical | rendah | pair TYP |

Panel (b) adalah metrik inti: RQ2 dan RQ3 seluruhnya tentang FPR_HN.

Whisker adalah interval Wilson 95%. Pada n kecil interval ini lebar dan **tidak
simetris** — itu benar, bukan bug. Rate 100% dari 4 pengamatan berbatas bawah
sekitar 40%.

Yang dicari: apakah ada konfigurasi yang menurunkan panel (b) tanpa menurunkan
panel (a). Kalau pola panel (a) dan (b) bergerak bersama, konfigurasinya hanya
menggeser ambang kecurigaan, bukan memperbaiki diskriminasi.

## Figure 2 — `fig_comparisons`

Figur keputusan. Satu kolom per model.

**Baris atas — FPR pada hard negative.** Tiap pasang batang satu hipotesis:
abu-abu baseline, biru variant.

| | Baseline → variant | Arah yang diprediksi | Guard recall |
|---|---|---|---|
| H2a | E0 → E3 | **naik** | tidak berlaku |
| H2b | E3-k2 → E4 | **turun** | berlaku |
| H3 | E4-noint → E4 | **turun** | berlaku |

H2a memprediksi kenaikan: menambahkan card yang seluruhnya malicious seharusnya
membuat model lebih sering menuduh. Itu premis yang dibantah H2b dan H3.

**Baris bawah — perubahan recall dalam poin persentase**, dengan interval bootstrap
95% per kampanye. Garis putus-putus adalah guard −5 pt.

- **Titik terisi**: guard berlaku. Variant hanya menang kalau tidak mengorbankan
  lebih dari 5 poin recall.
- **Titik berongga**: guard tidak berlaku. Hanya H2a, karena H2a tidak menawar
  FPR dengan recall.

Sebuah hipotesis didukung kalau **ketiganya** terpenuhi:

1. arah sesuai tabel di atas;
2. `p (Holm)` < 0,05 di sheet **comparisons**;
3. batas bawah interval recall tidak menembus garis guard — untuk H2b dan H3 saja.

Putusan akhirnya sudah dihitung dan ada di kolom `Verdict`.

**Uji yang dipakai McNemar,** yang hanya melihat pair **diskordan** — pair yang
berpindah putusan antara baseline dan variant. Dua konfigurasi bisa sama-sama
berada di FPR 40% tetapi salah di pair yang berbeda; itu bukan hasil nol. Kolom
`Discordant: baseline only` dan `Discordant: variant only` yang menunjukkannya,
bukan tinggi batangnya.

## Figure 3 — `fig_pareto`

Sumbu-x median latency (rendah baik), sumbu-y FPR pada hard negative (rendah baik).
Titik terisi Pareto-optimal, berongga terdominasi.

**Front dihitung atas tiga objektif — latency, FPR_HN, dan recall — sementara yang
digambar hanya dua.** Karena itu sebuah titik bisa tampak kalah di layar tetapi
tetap terisi: ia menang di recall, yang tidak punya sumbu. Recall-nya dilihat di
Figure 1 panel (a).

Hanya titik di front yang diberi label. Konfigurasi yang jatuh persis di titik yang
sama berbagi satu label, dipisah koma.

## Workbook `results.xlsx`

| Sheet | Isi |
|---|---|
| `rates` | satu baris per model × konfigurasi: tiga metrik dengan CI, n tiap subset, validitas JSON, latency median dan p95, rerata token |
| `comparisons` | enam uji konfirmatori dengan p mentah, p Holm, pasangan diskordan, Δrecall dan CI, serta putusan |
| `figures` | tiga blok bercaption berisi PNG yang sama |

`n MAL`, `n HN`, dan `n TYP` adalah **jumlah run**, bukan jumlah pair. Baca keduanya
bersama: rate 100% dengan `n MAL` = 1 tidak mengatakan apa pun, dan intervalnya di
Figure 1 yang menunjukkan itu.

## Kesalahan baca yang paling mudah terjadi

- **Membaca panel kosong sebagai data hilang.** Kosong berarti 0%.
- **Membaca recall 100% sebagai keberhasilan.** Periksa `n MAL` dulu.
- **Melompat ke selisih batang tanpa melihat whisker.** Dengan denominator kecil,
  hampir semua selisih tidak terbukti.
- **Menganggap guard membatasi H2a.** Tidak; titiknya digambar berongga.
- **Menganggap titik Pareto terisi pasti terbaik di layar.** Objektif ketiganya
  tidak digambar.
- **Membaca run yang gagal parse JSON sebagai kesalahan model.** Run tak valid
  dihitung `benign` (`--invalid-as`), sehingga muncul sebagai false negative pada
  MAL dan sebagai benar pada HN dan TYP. Kolom `JSON validity` yang memisahkannya.
