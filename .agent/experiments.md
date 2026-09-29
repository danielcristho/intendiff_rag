# Ringkasan eksperimen untuk agent

**Sumber kebenaran:**

- [docs/methodology.md](../docs/methodology.md) untuk prosedur.
- [docs/experiments.md](../docs/experiments.md) untuk jadwal, skema file, dan checklist.

File ini menerjemahkan keduanya ke spesifikasi yang bisa langsung dipakai saat
menulis kode. Kalau isinya berbeda, yang benar `docs/`, dan file ini yang harus
diperbarui.

**Status kode (2026-09-13):** runner dan prompt builder masih memakai E0–E4 lama.
Daftar perubahannya ada di `docs/experiments.md` §4.

## Spesifikasi konfigurasi

| ID | Isi hasil `retrieve` | Blok intent |
|---|---|---|
| E0-noint | `[]` | tidak ada |
| E0 | `[]` | ada |
| E2 | 1 card teratas dari seluruh KB | ada |
| E3 | 1 card malicious teratas | ada |
| E3-k2 | 2 card malicious teratas | ada |
| E4 | 1 card malicious teratas + 1 card benign teratas | ada |
| E4-noint | sama persis dengan E4 | tidak ada |

**Ranking kandidat:**

1. Buang card yang `name` atau `campaign`-nya sama dengan pair.
2. Hitung Jaccard pada `delta`, urutkan dari tertinggi.
3. Kalau skor seri, urutkan naik menurut `sha256(f"{pair_id}|{card_id}")`.

**Urutan card untuk E3-k2, E4, dan E4-noint:**

- Card malicious teratas ditaruh di posisi 1 kalau `zlib.crc32(pair_id.encode()) % 2 == 0`, dan di posisi 2 kalau tidak.
- Jangan pakai `hash()` bawaan Python, karena nilainya diacak per proses.

**Retrieval tidak pernah membaca intent.** Akibatnya E4 dan E4-noint selalu
mendapat card dan urutan yang identik.

## Yang masuk dan tidak masuk prompt

- **Tidak pernah masuk prompt:** `name`, `delta`, `label`, `source`, `campaign`.
- **Teks prompt** disalin verbatim dari methodology §6.1–§6.2, dalam bahasa Inggris. Jangan diparafrase.
- **Konfigurasi `*-noint`:** `INTENT_BLOCK` berupa string kosong.
- **Smart-diff** dipotong sekali per pair oleh pipeline data, dengan tokenizer Qwen2.5-Coder-3B-Instruct dan anggaran 28.000 token, lalu disimpan di `pairs.jsonl`. Runner tidak memotong ulang.

## Parsing

1. Cari `{` pertama, lalu baca satu objek JSON dengan `json.JSONDecoder().raw_decode`.
2. Output valid kalau `verdict` bernilai `malicious` atau `benign` (setelah strip dan lowercase), `evidence` berupa list string, dan `reason` berupa string.
3. `finish_reason == "length"` dihitung tidak valid.
4. Runner hanya menyimpan output mentah dan status valid. Kebijakan untuk output tidak valid diterapkan di skrip analisis.

## File data

| File | Ditulis oleh | Dibaca oleh |
|---|---|---|
| `data/samples.jsonl` | pengunduh sampel | pipeline data (checksum) |
| `data/pairs.jsonl` | pipeline data | runner, backend |
| `data/kb.jsonl` | pipeline data | runner |
| `data/dev.jsonl` | pipeline data | runner (dev set, warm-up) |
| `data/results.jsonl` | runner (append per run) | analisis, UI |
| `data/results.dev.jsonl` | runner | pemeriksaan validitas JSON (§6.4) |
| `data/audit_decisions.json` | backend | UI, analisis |

Definisi field ada di `docs/experiments.md` §3.

Contoh card **fiktif**:

```json
{"id": "card-b-001", "label": "benign", "campaign": "contoh-cli", "source": "manual",
 "delta": ["network", "host_info"],
 "intent": "Build tool CLI with opt-out anonymous usage statistics.",
 "behavior_chain": "command finishes → collect anonymous counters → HTTPS POST to documented endpoint",
 "code_excerpt": "if (!process.env.CONTOH_TELEMETRY_DISABLED) {\n  send(stats)\n}",
 "rationale": "Runs only after a user command, never at install time. Sends anonymous counters that the README documents and lets users disable."}
```

## Urutan run

1. **Cek pipeline:** `python -m pipeline selfcheck`.
2. **Jalankan server model:**
   `vllm serve <model> --port 8001 --dtype bfloat16 --max-model-len 32768 --seed 0`.
   Catat versi vLLM dan baris log memori bobot model.
3. **Warm-up:** kirim 3 request dari `data/dev.jsonl` ke `--out /dev/null`. Hasilnya tidak dicatat.
4. **Dev set:** `--pairs data/dev.jsonl --out data/results.dev.jsonl`. Periksa validitas JSON (§6.4).
5. **Gate G2:** bekukan desain. Perubahan setelah ini wajib dicatat di `docs/decisions.md`.
6. **Stage 1:** jalankan 7 konfigurasi dengan temperature 0.
7. **Stage 2:** konfigurasi `E0,E4`, temperature 0,7, top_p 0,8, top_k 20, seed 0, 1, 2. Flag untuk parameter ini masih harus ditambahkan, dan `run_key` wajib memuat temperature.
8. **Memori:** laporkan memori bobot dari log vLLM ditambah KV cache terhitung (methodology §9.3). Puncak nvidia-smi bukan metrik.

`--base-url` ditulis tanpa `/v1`, dan jangan pakai port 8000 karena sudah dipakai backend.

## Penanganan sampel yang aman

**Isolasi:** ekstraksi, smart-diff, extractor, dan Dolos dijalankan di
`docker run --network none`.

**Versi benign** — unduh dari registry, jangan di-install:

```bash
# paket ber-scope: tulis @scope%2Fnama
url=$(curl -s "https://registry.npmjs.org/<nama>/<versi>" | jq -r '.dist.tarball')
curl -sLo pkg.tgz "$url" && shasum -a 256 pkg.tgz
```

**Versi malicious:** `unzip -P infected <sampel>.zip -d <folder>`, dijalankan
di dalam container.

**Dilarang:**

- `npm install`, `npm ci`, `npx`, dan `node <file-sampel>`;
- `require()` atau `import` kode sampel;
- membuka URL atau IP yang muncul di dalam sampel.

## Keluaran skrip analisis

- **RQ1:** recall, FPR_TYP, dan FPR_HN dengan Wilson CI, untuk E0-noint dan E0 per model.
- **H2a, H2b, H3:** jumlah pair diskordan (b, c), p exact, p_Holm, Δrecall dengan bootstrap CI per kampanye, dan label hasil.
- **RQ4:** token, median dan p95 latency per konfigurasi, memori minimum terhitung per model, dan Pareto front.
- **Analisis sensitivitas:** output tidak valid dihitung sebagai `malicious`.
- **Subgroup:** delta kosong, `truncated`, pasca-rilis model (EA3), per kategori HN (EA1), per sumber, dan proporsi label card di E2.
