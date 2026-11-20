# Research summary

Operational summary of `docs/research.md` (RQs) and `docs/methodology.md`
(procedure), both on the `latex` branch (`git show latex:docs/research.md`).
It exists so a change to the code or the text does not break the design. When
it disagrees with those documents, they are right and this file is updated.

## Core question

Can a 3–4B open-weight LLM tell a malicious npm update from a legitimate update
that behaves similarly? Do a contrasting benign example and the package's
intent reduce its false positives?

## RQs, configurations and endpoints

| RQ | Compared | Endpoint | Answered by |
|---|---|---|---|
| RQ1 | DIFF, DIFF+I | recall, FPR_TYP, FPR_HN with Wilson CI | descriptive |
| RQ2a | DIFF+I+M vs DIFF+I | FPR_HN | exact McNemar + Holm |
| **RQ2b (primary)** | DIFF+I+MB vs DIFF+I+MM | FPR_HN, recall margin −5 points | exact McNemar + Holm; recall bootstrap by campaign |
| RQ3 | DIFF+I+MB vs DIFF+MB | FPR_HN, recall margin −5 points | as RQ2b |
| RQ4 | every configuration | tokens, median/p95 latency, computed GPU memory | descriptive |

There are only **six confirmatory tests**: H2a, H2b and H3 for each of the two
models. Everything else is exploratory (EA1–EA5). Outcome labels ("supported",
"partially supported", …) are defined in `docs/research.md` §5.

Since D99 the evaluation runs on dataset labels and every comparison is
reported descriptively; see [status.md](status.md).

## Invariants

| Invariant | If broken |
|---|---|
| System prompt and smart-diff identical across configurations | every comparison is void |
| DIFF+I+MM and DIFF+I+MB both carry 2 cards | RQ2b cannot separate the contrastive effect from the number of examples |
| `DIFF+MB` only removes the intent block from `DIFF+I+MB` | RQ3 is void |
| Intent is taken from v_{t−1} | an attacker could steer intent through the README of v_t |
| Retrieval excludes cards from the pair's package or campaign | leakage; RQ2 and RQ3 are void |
| Card order in DIFF+I+MM and DIFF+I+MB is counterbalanced by the same rule (top malicious card in the same position) | RQ2b is confounded by recency bias |
| Retrieval never reads intent | DIFF+I+MB and DIFF+MB get different cards; RQ3 is void |
| Package name and capability delta never enter the prompt | RQ1 would measure the extractor or memorisation, not reading the smart-diff (D25, D26) |
| Smart-diff is truncated once per pair with the Qwen2.5-Coder-3B tokenizer and used as-is by every configuration and model | inputs differ between configurations or models |
| Prompt text is copied verbatim from methodology §6 | the tested prompt is not the reported one |
| Capability delta is extracted automatically by the same extractor for pairs and cards | human judgement leaks into the model input |
| Stage 1 uses temperature 0 and sequential requests | not reproducible; RQ4 latency is wrong |
| The runner stores raw output; the invalid-output policy is applied in analysis | the D18 sensitivity analysis cannot run |
| The prompt never names the hard-negative categories | FPR_HN is optimistic (D17) |

## Never

- Tune a prompt, configuration or capability list after seeing test-set results. After Gate G2, every change is recorded in `docs/decisions.md` and every configuration is re-run.
- Write that the method is "better" than RogueOne, IntelGuard or Wyss et al. The data and setups differ; their numbers are context for the Discussion only (D23).
- Write "no effect" from a non-significant result. State the design's detection limit instead.
- Add a confirmatory test without updating the Holm correction and `docs/decisions.md`.
- Claim intent mismatch as a new idea; what is new is measuring it (D3). The main novelty claim is Gap 2.
- Run, install, or contact an endpoint from a malicious sample.

## Terms

| Term | Meaning |
|---|---|
| pair | one update `pkg@v_{t−1} → pkg@v_t` |
| MAL / HN / TYP | malicious / hard-negative / typical subset |
| hard negative | a benign update that adds a sensitive capability for a documented legitimate purpose |
| capability delta | capabilities present in v_t but not in v_{t−1} |
| intent profile | `description`, `keywords`, the start of the README and `scripts` of v_{t−1} |
| card | a KB example labelled malicious or benign, holding intent, delta and a short rationale |
| campaign | pairs sharing an actor or payload (e.g. Shai-Hulud); the bootstrap unit and the retrieval-exclusion unit |
| FPR_HN | share of HN pairs given the verdict `malicious` |

## Writing the manuscript

- Main reference: Wyss et al. (RAID 2025). Quotable facts and corrections to the P1 slides are in `docs/references.md`.
- Motivating examples: chalk/debug, Shai-Hulud, axios. CVE-2025-66478 is not a malicious update.
- Positioning: triage of dependency updates before an advisory is published, not IT governance audit.
- Positioning against RogueOne: [rogueone.md](rogueone.md).
