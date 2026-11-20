# Experiment specification

Turns `docs/methodology.md` (procedure) and `docs/experiments.md` (schedule,
file schemas, checklist), both on the `latex` branch, into a spec the code can
follow directly. When this file disagrees with them, they are right and this
file is updated. Progress and frozen releases are in [status.md](status.md).

## Configurations

| ID | `retrieve` returns | Intent block |
|---|---|---|
| DIFF | `[]` | no |
| DIFF+I | `[]` | yes |
| DIFF+I+M | top malicious card | yes |
| DIFF+I+MM | top 2 malicious cards | yes |
| DIFF+I+MB | top malicious card + top benign card | yes |
| DIFF+MB | exactly as DIFF+I+MB | no |

The table lives in `pipeline/configs.py`; the superseded `E0`–`E4` ids are rejected.

**Candidate ranking:**

1. Drop cards whose `name` or `campaign` equals the pair's. Since D88, also drop the dependency names in `delta_evidence.dependency_change` and `retrieval_exclude_names`. This is a metadata filter, not intent; sidecars must be merged into the pair explicitly. Extractor evidence is limited, so do not claim every transitive, aliased or cloned dependency is covered.
2. Score by Jaccard on `delta`, highest first.
3. Break ties ascending by `sha256(f"{pair_id}|{card_id}")`.

**Card order for DIFF+I+MM, DIFF+I+MB and DIFF+MB:**

- The top malicious card goes in position 1 when `zlib.crc32(pair_id.encode()) % 2 == 0`, otherwise in position 2.
- Never use Python's built-in `hash()`; it is randomised per process.

**Retrieval never reads intent**, so DIFF+I+MB and DIFF+MB always get the same
cards in the same order.

## What enters the prompt

- **From the pair, never in the prompt:** `name`, `delta`, `label`, `gold_evidence`, `subset`, `category`, `campaign`, `source`.
- **From a card, never in the prompt:** `id`, `delta`, `campaign`, `source`. The card label **is** shown (`Example 1 (label: MALICIOUS)`), because that is what makes the examples contrastive (methodology §5.1, §6.2).
- **Prompt text** is copied verbatim from methodology §6.1–§6.2, in English. Never paraphrase it.
- **Configurations without `I`** (`DIFF`, `DIFF+MB`): `INTENT_BLOCK` is the empty string.
- **Smart-diff** is truncated once per pair by the data pipeline, with the Qwen2.5-Coder-3B-Instruct tokenizer and a 28,000-token budget, and stored in `pairs.jsonl`. The runner never truncates again.

## Parsing

1. Find the first `{` and read one JSON object with `json.JSONDecoder().raw_decode`.
2. Output is valid when `verdict` is `malicious` or `benign` (after strip and lowercase), `evidence` is a list of strings and `reason` is a string. Since D101 the schema is enforced through structured output (`pipeline/output_schema.py`).
3. `finish_reason == "length"` counts as invalid.
4. The runner stores raw output and validity only. The invalid-output policy is applied in analysis.

## Data files

| File | Written by | Read by |
|---|---|---|
| `data/wanted.jsonl` | candidate collection | `samples.py fetch` |
| `data/samples.jsonl` | `samples.py fetch` | `samples.py extract`, `dataset.py` (checksums) |
| `data/pairs.manifest.jsonl` | collection + labelling | `dataset.py` |
| `data/pairs.jsonl` | `dataset.py` | runner, backend |
| `data/kb.jsonl` | data pipeline | runner |
| `data/dev.jsonl` | data pipeline | runner (dev set, warm-up) |
| `data/results.jsonl` | runner (append per run) | analysis, UI |
| `data/results.dev.jsonl` | runner | JSON validity check (§6.4) |
| `data/audit_decisions.<annotator>.json` | backend, one file per annotator | UI, analysis |

Field definitions: `docs/experiments.md` §3.

A **made-up** card:

```json
{"id": "card-b-001", "label": "benign", "campaign": "example-cli", "source": "manual",
 "delta": ["network", "host_info"],
 "intent": "Build tool CLI with opt-out anonymous usage statistics.",
 "behavior_chain": "command finishes → collect anonymous counters → HTTPS POST to documented endpoint",
 "code_excerpt": "if (!process.env.EXAMPLE_TELEMETRY_DISABLED) {\n  send(stats)\n}",
 "rationale": "Runs only after a user command, never at install time. Sends anonymous counters that the README documents and lets users disable."}
```

## Run order

**Data chain** (before the model is up):

1. **Collect candidates** per methodology §3.1–§3.3 into `data/wanted.jsonl` (versions to download) and `data/pairs.manifest.jsonl` (pairs with metadata and labels). TYP and path A:
   `uv run pipeline/typical.py sample --popular <list> --random <list> --out data/typ.jsonl --pool data/pool.jsonl`,
   then `uv run pipeline/typical.py screen --pool data/pool.jsonl --out data/hn_candidates.jsonl`.
   Path B uses `collect.py search` and `collect.py pairs`.
   HN split: `uv run pipeline/hardnegative.py --verified data/hn_verified.jsonl --test data/hn_test.jsonl --cards data/hn_cards.jsonl`.
   Malicious cards: `uv run pipeline/kb.py select --pool <malicious-intent-pool> --pairs data/pairs.jsonl --out data/kb.mal.jsonl`;
   an annotator fills `intent`, `behavior_chain`, `code_excerpt` and `rationale`,
   then `uv run pipeline/kb.py fit --cards data/kb.jsonl --out data/kb.jsonl` bounds their size.
2. **Fetch** (needs the network, outside the container):
   `uv run pipeline/samples.py fetch --wanted data/wanted.jsonl --out data/samples.jsonl`.
3. **Extract** (no network, inside the container):
   `uv run pipeline/samples.py extract --manifest data/samples.jsonl --into work`.
4. **Assemble pairs.** The dev set uses the same path with a different manifest (§3.5, 10 pairs):
   `uv run pipeline/dataset.py --manifest data/pairs.manifest.jsonl --samples data/samples.jsonl --out data/pairs.jsonl`.
   The diff is truncated here, once per pair.
5. **Gate G1:** compare per-subset counts with their minimum and record it in `docs/decisions.md`.

**Inference:**

6. **Check the runner:** `uv run pipeline/runner.py --selfcheck`.
7. **Start the model server:** `vllm serve <model> --port 8101 --dtype bfloat16 --max-model-len 32768 --seed 0`.
   Record the vLLM version and the model-weight memory line from its log.
8. **Warm-up:** 3 requests from `data/dev.jsonl` to `--out /dev/null`; not recorded.
9. **Dev set:** `--pairs data/dev.jsonl --out data/results.dev.jsonl`; check JSON validity (§6.4).
10. **Gate G2:** freeze the design. Every later change is recorded in `docs/decisions.md`.
11. **Stage 1:** the six configurations at temperature 0.
12. **Decoding ablation (D111, replaces Stage 2):** T {0, 0.3, 0.7, 1.0} × seed {0, 1, 2}, top_p 1,
    both main models, six configurations:
    `uv run pipeline/sampling_batch.py --release data/evaluation/sampling-ablation-20261109`,
    then `uv run pipeline/sampling_report.py --release data/evaluation/sampling-ablation-20261109`.
13. **Memory:** report model-weight memory from the vLLM log plus the computed KV cache (methodology §9.3). An nvidia-smi peak is not the metric.

`--base-url` has no `/v1` suffix and defaults to port 8101.

## Safe sample handling

**Isolation:** extraction, smart-diff, the extractor and Dolos run in
`docker run --network none`. Downloads happen outside the container, so the
order is `samples.py fetch` (network) then `samples.py extract` (no network,
D65). `extract` rejects archive members that escape the target directory or
are links, and verifies checksums before opening an archive.

**Benign versions:** for Wyss pairs take both sides from the replication
package (D59); for other sources download from the registry, never install:

```bash
# scoped packages: write @scope%2Fname
url=$(curl -s "https://registry.npmjs.org/<name>/<version>" | jq -r '.dist.tarball')
curl -sLo pkg.tgz "$url" && shasum -a 256 pkg.tgz
```

**Malicious versions:** `unzip -P infected <sample>.zip -d <dir>`, inside the container.

**Forbidden:**

- `npm install`, `npm ci`, `npx`, `node <sample-file>`;
- `require()` or `import` of sample code;
- opening any URL or IP found inside a sample.

## Analysis outputs

- **RQ1:** recall, FPR_TYP and FPR_HN with Wilson CI, for DIFF and DIFF+I per model.
- **H2a, H2b, H3:** discordant pair counts (b, c), exact p, p_Holm, Δrecall with campaign-bootstrap CI, and the outcome label.
- **RQ4:** tokens, median and p95 latency per configuration, minimum computed memory per model, and the Pareto front.
- **Sensitivity:** invalid output counted as `malicious`.
- **Subgroups:** empty delta, `truncated`, post-model-release (EA3), per HN category (EA1), per source, and the label share of the top card if the KB were one mixed pool (computed without inference, D61).
