# IntentDiff-RAG

[![ci](https://github.com/danielcristho/intendiff_rag/actions/workflows/ci.yml/badge.svg)](https://github.com/danielcristho/intendiff_rag/actions/workflows/ci.yml)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/danielcristho/intendiff_rag/badge)](https://scorecard.dev/viewer/?uri=github.com/danielcristho/intendiff_rag)

Measures how a package's stated purpose and in-context reference examples shift
what locally run language models flag as a malicious npm update.

## Highlights

- Without examples, LLMs missed over half of attacks or flagged most typical updates.
- A benign in-context example raised false alarms in three of six models.
- Phi-4-mini's FPR drop with a benign example came with a lower TPR estimate.
- Intent lowered false alarms in two models and raised them in two others.
- For 2/3 of malicious updates, examples were chosen at random by a hash tie-break.

## Setup

**Data.** 129 malicious updates (MAL) from 98 campaign clusters and 1,868
typical updates (TYP). MAL labels come from the dataset sources; TYP updates
are assumed benign after advisory filtering.

**Configurations.** All six use the same smart-diff.

| Configuration | Intent | Reference examples |
|---|---|---|
| `DIFF` | no | none |
| `DIFF+I` | yes | none |
| `DIFF+I+M` | yes | one malicious |
| `DIFF+I+MM` | yes | two malicious |
| `DIFF+I+MB` | yes | one malicious, one benign |
| `DIFF+MB` | no | one malicious, one benign |

**Models.** Qwen3-4B-Instruct-2507, Qwen2.5-Coder-3B-Instruct,
Qwen2.5-Coder-7B-Instruct, Phi-4-mini-instruct, Llama-3.1-8B-Instruct, and
Granite-3.3-8B-Instruct, served with vLLM on one RTX 5090. Qwen3-8B failed the
dev gate (49/60 valid responses). Six models × six configurations × 1,997 pairs
gives 71,892 responses.

**Analyses.**

1. **Baseline:** `DIFF` and `DIFF+I`.
2. **Reference examples:** `DIFF+I` → `DIFF+I+M` (add a malicious example) and
   `DIFF+I+MM` → `DIFF+I+MB` (replace the second example with a benign one).
3. **Intent:** `DIFF+MB` → `DIFF+I+MB`.
4. **Cost:** token count and request latency.

Contrasts are paired on the same model and pairs, with campaign-level bootstrap
intervals and exact permutation tests under Holm correction.

## Repository layout

| Path | Contents |
|---|---|
| `pipeline/` | experiment runner; configurations live in `pipeline/configs.py` |
| `backend/`, `frontend/` | label-audit and error-analysis UI (Rust + React) |
| `data/` | pair manifests, KB, and evaluation outputs |
| `labs/latex/` | manuscript sources, on the `latex` branch (`git switch latex`) |
| `.agent/` | design summary, conventions, architecture and status; full `docs/` (in Indonesian) is on the `latex` branch |

## Running it

### With Docker

```bash
docker compose up -d --build   # UI on http://localhost:5174, API on :8100
docker compose down
```

Plain `up` starts only the backend and the frontend. The UI proxies `/api` to the
backend, and the backend serves `./data`, falling back to the sample pairs. No
`.env` is needed. To change ports or the bind address, copy `.env.example` to
`.env`. For vLLM on :8101 (needs an NVIDIA GPU), run
`docker compose --profile model up -d`. See
[deployments/README.md](deployments/README.md).

### Locally

```bash
make venv      # Python env from uv.lock
make install   # frontend dependencies
make backend   # terminal 1: API on :8100
make ui        # terminal 2: http://localhost:5174
make test      # backend, frontend and pipeline; CI runs the same targets

uv run pipeline/runner.py --model Qwen/Qwen3-4B-Instruct-2507   # needs vLLM on :8101
uv run pipeline/runner.py --selfcheck
```
