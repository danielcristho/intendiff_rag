# IntentDiff-RAG

Research: *Detecting Malicious npm Updates with Small Open-Weight LLMs* (ITS).

**This is a research experiment, not a production scanner.** Judge every
technical decision by "does this answer an RQ", not by feature completeness.

## Rules

- **Malicious samples are analysed statically only.** Never execute them, never `npm install` them, never run their lifecycle scripts. No network call to any endpoint found inside a sample.
- **`.ref/` is read-only** — reference material, not project code. Do not edit it.
- **Report numbers as they come out.** A configuration losing to the baseline is a result, not a bug to tune until it wins.
- **The design in force lives in `docs/`, not in the P1 slides.** The proposal's RQs were revised on 2026-09-13. Every design change is recorded in `docs/decisions.md`.
- **The design freezes at Gate G2** (end of M4). After that, any change to a prompt, configuration, capability list, or decision rule must be recorded in `docs/decisions.md` and every configuration re-run. Never tune a prompt against test-set results.
- Eight-week scope. Out of scope unless asked: CI integration, dynamic sandbox execution, fine-tuning, closed models.

## Code style

Everything inside a source file is **English** — comments, test names,
identifiers — even though the research documents in `docs/` and `.agent/` are in
Indonesian. Code outlives the language its authors discussed it in.

**Comments follow the nine rules from Stack Overflow's "Best practices for
writing code comments"** (2021-12-23). The ones that bite hardest here:

1. **Never duplicate the code.** A comment that restates the signature is noise
   — delete it. `# sha256_text returns a hex digest` above `def sha256_text`
   tells the reader nothing they cannot already see.
2. **A comment never excuses unclear code.** Rename the thing instead.
3. **If the comment is hard to write, the code is probably wrong.**
4. **Dispel confusion, do not add it.**
5. **Explain unidiomatic code.** This is where comments earn their keep — a
   trade-off, a constraint, a trap someone would otherwise reintroduce.
6. **Link the source of copied code.**
7. **Link an external reference only when the code cannot be read without it** —
   a file-format spec, a copied algorithm. Never narrate the research: no RQ
   numbers, no hypotheses, no "why the study needs this". A reader of
   `pipeline/` is reading code, and the design lives in `docs/`.
8. **Comment when fixing a bug**, saying what broke.
9. **Mark incomplete work.** `TODO` for a gap; `// ponytail:` for a deliberate
   shortcut, naming its ceiling and upgrade path; `// SAFETY:` on every
   `unsafe` block.

**Keep them short** — one or two lines. A paragraph in a source file is a sign
the explanation belongs in `docs/`. Module docstrings say how to run the file
and nothing more.

When a comment does earn its place on a declaration, start it with the
declaration's own name (`// keep filters ...`, never `// Filters ...`) so the
line reads on its own. That is a format for the comments worth writing, not a
reason to write one everywhere.

**Clean code.** One reason to change per file; extract past roughly 150 lines
or a second audience. Name things for what they are — no `data`, `info`,
`handle`, `manager`. Guard clauses first, happy path unindented. No parameter,
interface, or config key with one caller and one value.

**SOLID.** Single responsibility is the one that earns its keep: handlers
route, a store reads and writes, a clock formats time. If a module needs "and"
to describe it, split it. Do not add a trait or interface with a single
implementation to satisfy the letter of the rule. Open/closed here means
data-driven — a new configuration is a new table entry, not a new branch in
five files.

**DRY** applies to duplicated *knowledge*, not duplicated characters. Two
functions that look alike but change for different reasons stay apart. One rule
is duplicated on purpose, because it spans a language boundary:
`valid_annotator` in `backend/src/store.rs` and `validAnnotator` in
`frontend/src/lib/annotator.ts` encode `[A-Za-z0-9_-]{1,32}` and guard a
filename. **Change one, change the other**, and keep the test in each.

**Tests.** Non-trivial logic leaves one runnable check — a Rust `#[cfg(test)]`
module, a Vitest file, or a `--selfcheck` flag. Name a test after the invariant
it pins, not the function it calls.

## Running it

Two terminals (`make help` lists the targets):

```
make backend   # terminal 1, :8100 — must be up first
make ui        # terminal 2, http://localhost:5174
make test      # backend, frontend and runner in one go
```

Or through Docker, where nginx serves the UI and proxies `/api`:

```
cp .env.example .env               # set APP_UID/APP_GID from `id -u` / `id -g`
docker compose up -d backend frontend    # http://localhost:5174, no GPU needed
docker compose --profile model up -d     # adds vLLM on :8101, needs an NVIDIA GPU
```

vLLM runs from the official image rather than a Dockerfile of ours. Default
model is `Qwen2.5-Coder-3B`; Qwen3-4B does not fit in 12 GiB (D44).

Deploying to the GPU host: `deployments/README.md`. vLLM pre-allocates VRAM as a
fraction of the **total** card, so `VLLM_GPU_UTIL` must be sized against what is
actually free or it will starve `production-service`.

**Ports on the GPU host are crowded.** 8000 belongs to production-service, plus
8080, 8081, 5433, 9400 and 18888. Hence backend on 8100 and vLLM on 8101,
published via `BIND_ADDR`. Run `docker ps` before changing ports in `.env`.

## Components

`frontend/` — research tooling: label audit (M1-2) and error analysis (M7-8).
Vite + React + TS + Tailwind. Structure follows `.ref/spider/frontend`; the
design language (colour tokens, flat components) follows `.ref/cloudx_ui`.

```
cd frontend && pnpm install
pnpm dev           # http://localhost:5174 (needs the backend running)
pnpm test          # filter and aggregation logic
pnpm build         # tsc --noEmit && vite build
```

`pipeline/` — experiment runner. Batch, not a service: read pairs, run each
configuration against vLLM's OpenAI-compatible endpoint (D46), append one line
per run. The code still follows the superseded E0–E4 scheme; the revised
configurations and the migration checklist are in `docs/methodology.md` and
`docs/experiments.md` §4.

```
python pipeline/runner.py --model Qwen/Qwen3-4B-Instruct-2507
python pipeline/runner.py --selfcheck
```

Resumable — runs already in `results.jsonl` are skipped, so the batch can be
stopped at any time. Sequential on purpose: RQ4 reports median and p95 latency,
and those numbers are wrong if requests overlap on the server.

GPU memory is not measured by the runner. Never use an nvidia-smi peak as the
metric: vLLM pre-allocates per `--gpu-memory-utilization`. `docs/methodology.md`
§9.3 (D41) defines what to report instead.

`backend/` — API for the audit UI. Rust + axum.

```
cd backend && cargo run -- --data-dir ../data --port 8100
cargo test
```

Reads `data/pairs.jsonl` (falling back to `data/pairs.sample.jsonl`; the KB is
`data/kb.jsonl`) — input datasets are never modified. It serves files, not a
database: the Python runner and the backend read and write the same directory.

**Double annotation (§8):** decisions are written per annotator to
`data/audit_decisions.<annotator>.json`, not to one shared file. The UI gates on
identity before labelling, and `GET /api/annotators` reports counts only, never
labels, so labelling stays independent.

Decision writes are guarded by a mutex and land through an atomic rename, so two
nearby clicks cannot overwrite each other and a process dying mid-write cannot
truncate the file.

The frontend proxies `/api` to port 8100, so the backend must be up first. The
runner defaults to `--base-url http://localhost:8101`, the vLLM port.

## Documents

- `docs/research.md` — problem, positioning, gaps, RQ1–RQ4, hypotheses, decision rule, threats to validity
- `docs/methodology.md` — the final procedure: data, smart-diff, extractor, intent, KB and retrieval, verbatim prompts, inference, metrics, statistics
- `docs/experiments.md` — execution: timeline and gates, run volume, file schemas, implementation checklist
- `docs/figures.md` — how to read the figures and the workbook, and the misreadings to avoid
- `docs/references.md` — reference status (checked against the originals), quotable facts, corrections to the P1 slides
- `docs/decisions.md` — dated decision log; add an entry whenever the design changes
- `labs/refrences/P1_Metodologi Penelitian.pdf` — the original proposal; its scope still holds, its RQs are superseded by `docs/research.md`
- `.agent/research.md` — agent summary: RQ to configuration, invariants, prohibitions, terminology
- `.agent/experiments.md` — configuration spec for the code, file schemas, run order, safe sample handling
- `.agent/rogueone.md` — position relative to RogueOne: ideas taken and skipped, quotable numbers (not re-run, D20)

`docs/` is the source of truth; `.agent/` is its operational summary. When they
disagree, `docs/` is right and `.agent/` gets updated.
