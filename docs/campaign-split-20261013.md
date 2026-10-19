# Clustering gabungan dan usulan partisi TYP/HN — 13 Oktober 2026

**Status: usulan partisi, bukan test set beku. Tidak ada label gold, inferensi
LLM, atau eksekusi kode paket.** Keputusan aturan: D96.

## Yang dijalankan

- Material kampanye (§3.6) untuk 2.420 kandidat TYP/HN baru dan regenerasi
  25.073 item lama (875 MAL kandidat + 24.198 pool KB), di container
  `intendiff-preprocess:campaign-v1` dengan `--network none`.
- Regenerasi lama diverifikasi baris per baris terhadap material 29 September:
  nol selisih ID/peran/laporan/kode; gabungan hash non-trivial + trivial sama
  dengan hash lama. 6.985 item lama memiliki file trivial.
- Fingerprint Dolos (k=70, w=17) 27.493 item, nol kegagalan; clustering pada
  ambang 0,5 dan 0,8 dengan aturan D96 dan aturan lama sebagai sensitivitas.

| Aturan | Klaster @0,5 | Klaster @0,8 | Klaster terbesar |
|---|---:|---:|---:|
| D96 (file < 64 byte setelah strip diabaikan pada kriteria b) | 7.178 | 7.702 | 12.269 |
| Lama (§3.6 apa adanya) | 5.982 | 6.433 | 14.718 |

Mega-klaster KB tetap besar di D96 (12.269 item): tautan file trivial bukan
satu-satunya penyebabnya. Ini properti pool KB, tidak disetel ulang.

## Usulan partisi

`holdout_eligible` = tidak terpapar menurut identitas/nama/dependency **dan**
kampanyenya tidak memuat item terpapar (MAL kandidat seluruhnya terpapar).

| | Jumlah |
|---|---:|
| Kandidat review | 2.420 |
| Dev (terpapar) | 274 |
| Calon test TYP (tanpa overlap HN) | 1.896 — popular 704, random 814, stream 378 |
| HN calon holdout, menunggu anotasi | 250 (108 juga TYP) |
| Calon holdout TYP termasuk overlap HN | 2.004 |

- Alasan dev (dapat tumpang tindih): pair terpapar 140, paket terpapar 151,
  dependency terkait 52, **kampanye bersama item terpapar 91**. Clustering
  sendiri menambah 79 item ke dev (58 TYP, 31 HN) di luar pemeriksaan identitas.
- Sensitivitas aturan lama: 1.987 TYP / 244 HN eligible. Hanya 20 item
  berubah status, semuanya menjadi eligible di D96.
- Calon holdout tersebar di 1.893 kampanye TYP dan 250 kampanye HN; kampanye
  eligible terbesar hanya 3 item. Tiga item eligible berbagi kampanye dengan
  card KB; retrieval akan mengecualikan card tersebut (§5.2), bukan kebocoran label.

## Batas

- HN 250 belum HN: tujuan sah, kategori, dan split test/KB per §3.3 menunggu
  anotasi A/B. Jumlah ini masih di bawah 300–500 target desain D94.
- TYP diasumsikan benign (Wyss); FPR per strata dilaporkan terpisah.
- Klon belum diperiksa terhadap pretraining model; bebas klon di sini hanya
  relatif terhadap pool lokal.
- MAL baru tetap nol; seluruh MAL tetap dev.

## Artefak dan reproduksi

`data/acquisition/campaigns-20261013/`: `combined-d96.json`,
`combined-pre-d96.json`, `split-proposal.jsonl`, `split-summary.json`,
`materials-verification.json`, log, `tests.log`.

```bash
python pipeline/campaign_materials.py --review REVIEW_TYP REVIEW_HN --out data/work/audit/expansion.campaign-items.jsonl
python pipeline/campaign_materials.py --acquisition data/acquisition --inventory datadog.inventory-full.jsonl --advisories campaign-advisories-full.jsonl --out data/work/audit/full-d96.campaign-items.jsonl
python pipeline/campaign_fingerprints.py --items data/work/audit/full-d96.campaign-items.jsonl data/work/audit/expansion.campaign-items.jsonl --cache data/work/audit/fingerprints --hash-rule d96 --out data/acquisition/campaigns-20261013/combined-d96.json
python pipeline/expansion_split.py --review REVIEW_TYP REVIEW_HN --campaigns .../combined-d96.json --sensitivity .../combined-pre-d96.json --exposure data/acquisition/expansion-20261012/exposure-registry.jsonl --out data/acquisition/campaigns-20261013
```
Tiga perintah pertama dijalankan dalam container tanpa jaringan.
