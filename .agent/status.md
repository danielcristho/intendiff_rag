# Experiment status

Where the study stands, what is frozen, and what is still open. The decision
log (`docs/decisions.md`) and every report live under `docs/` on the `latex`
branch: `git show latex:docs/<file>`. When this file and `docs/` disagree,
`docs/` is right.

## Current position

- **Main evaluation (D99–D101) is complete.** Six configurations × two 3–4B
  models (Qwen3-4B-Instruct-2507, Qwen2.5-Coder-3B-Instruct), 1,901 test pairs,
  75 KB cards, 22,812 generations, structured output (D101). Valid JSON: Qwen3
  95.6 %, Qwen2.5 99.5 %. Report: `docs/source-labelled-results-20261015.md`.
- **Extension to five more models (D102) is complete** for the models that
  passed the dev gate (≥ 90 % valid JSON). Qwen3-8B failed the gate (49/60,
  81.67 %) and is excluded; the threshold is not lowered for it.
- **Additional MAL (D103–D106) is evaluated**: 96 pairs / 65 campaigns on all
  six eligible models (3,456 responses). The manuscript reports the 129 MAL
  (33 + 96) as one set (D106).
- **Decoding ablation (D111) is complete**: temperature {0, 0.3, 0.7, 1.0} ×
  seed {0, 1, 2} on the two main models, 24 cells, 287,568 responses.
  Descriptive only; the main tables stay at T = 0, seed 0. Report:
  `docs/sampling-ablation-results-20261112.md`.
- **Headline result, reported as it came out:** going from MM to MB raised FPR
  on four of six models; the two models whose FPR fell also lost TPR. No
  configuration improved both for all six models at the point estimates. All
  intervals are descriptive, not confirmatory.

## Labels and gates

- **Labels come from the datasets (D99).** MAL uses source labels, TYP is
  assumed benign, HN is pending: HN verdicts are reported as alarms, never as
  FPR. Double human annotation is not a prerequisite any more.
- G1/G2 are judged on source, split, format and pins (D99), not on human gold.
- The manuscript has no RQ structure (D110); `docs/research.md` keeps the RQs
  as the study design.

## Frozen; do not edit or re-run

| Directory | Decision |
|---|---|
| `data/preparation/source-labelled-20261014/` | D99 cohort and KB |
| `data/preparation/final-rag-20261014/` | D98 HN normalisation |
| `data/evaluation/source-rag-v3-20261015/` | D101 main run (`protocol.json` `test_released: true`) |
| `data/evaluation/source-rag-extra-20261016/` | D102 five-model extension |
| `data/evaluation/source-rag-mal-20261018/` | D105 additional MAL |
| `data/evaluation/full-method-20261012/` | D92 full rerun |
| `data/evaluation/sampling-ablation-20261109/` | D111 decoding ablation |

Each release keeps a pinned copy of the code it ran under `code/`. Fix the live
module in `pipeline/`, never the pinned copy. Earlier exploratory runs (D81–D90)
are archived on the `latex` branch.

## Open

- No human gold labels and no verified human-written KB cards.
- FPR on hard negatives is not measured; HN results are alarms only.
- The dependency-context diagnoses (D88–D90) ran on small subsets; they are not
  a full dependency or RAG evaluation.
- Six confirmatory tests (H2a, H2b, H3 × two models) from `docs/research.md`
  were not run as confirmatory tests; every reported comparison is descriptive.

## Timeline

| Decision | What | Report in `latex:docs/` |
|---|---|---|
| D81 | exploratory DIFF / DIFF+I baseline, 973 pairs, two models | `comparison-20260929.md` |
| D82 | output budget 2,048 vs 512 tokens | `output-budget-20260930.md` |
| D83 | Qwen2.5-Coder-7B and Qwen3-8B | `model-scale-20260930.md` |
| D84 | Phi-4-mini and Llama-3.1-8B | `model-families-20261001.md` |
| D85 | output format and evidence verification on HN dev | `evidence-dev-results-20261001.md` |
| D86–D87 | mixed dev set; D85 interventions on MAL | `mixed-validation-results-20261011.md` |
| D88 | dependency context as a conditional version test | `dependency-context-results-20261012.md` |
| D89 | dependency contents with parallel conditional instructions | `dependency-generalization-results-20261012.md` |
| D90 | Granite 3.3 8B on the D89 conditions | `granite-dependency-results-20261012.md` |
| D91–D92 | full rerun after diff, schema and verifier changes | `full-method-20261012.md` |
| D94–D95 | dataset expansion: TYP stream, HN candidates | `dataset-expansion-results-20261013.md` |
| D96 | combined clustering and split proposal | `campaign-split-20261013.md`, `campaign-audit-20261013.md` |
| D97–D98 | independent MAL sources; final RAG preparation | `final-rag-preparation-20261014.md` |
| D99–D101 | source-labelled main evaluation, structured output | `source-labelled-final-20261014.md`, `source-labelled-results-20261015.md` |
| D102 | five more models | `source-rag-extension-20261016.md` |
| D103–D105 | additional MAL acquisition and evaluation | `mal-expansion-20261016.md`, `mal-expansion-20261017.md`, `mal-evaluation-20261018.md` |
| D106–D110 | manuscript reporting decisions | `manuscript-audit-20261018.md` |
| D111 | temperature × seed ablation, replaces Stage 2 | `sampling-ablation-20261109.md`, `sampling-ablation-results-20261112.md` |
