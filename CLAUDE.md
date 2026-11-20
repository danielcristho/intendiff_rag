# IntentDiff-RAG

Research: *Detecting Malicious npm Updates with Small Open-Weight LLMs* (ITS).
**A research experiment, not a production scanner.** Judge every technical
decision by "does this answer an RQ", not by feature completeness.

## Rules

- **Malicious samples are analysed statically only.** Never execute them, never `npm install` them, never run their lifecycle scripts, never call an endpoint found inside a sample.
- **`.ref/` is read-only** reference material.
- **Report numbers as they come out.** A configuration losing to the baseline is a result, not a bug to tune.
- **The design is summarised in `.agent/`.** The full documents and the decision log (`docs/decisions.md`) are on the `latex` branch; every design change gets an entry there.
- **The design is frozen after Gate G2.** A change to a prompt, configuration, capability list or decision rule is recorded in `docs/decisions.md` and every configuration is re-run. Never tune against test-set results.
- Out of scope unless asked: CI integration, dynamic sandboxing, fine-tuning, closed models.

## Running it

```
make venv      # Python env from uv.lock
make backend   # :8100, must be up first
make ui        # http://localhost:5174
make test      # backend, frontend and pipeline checks; must pass before a push
```

Docker: `docker compose up -d backend frontend`; add `--profile model` for vLLM
on :8101 (needs an NVIDIA GPU). GPU host: `deployments/README.md`.

## Read before changing things

| File | When |
|---|---|
| `.agent/conventions.md` | writing code, comments, tests or commits |
| `.agent/architecture.md` | touching `pipeline/`, `backend/`, `frontend/`, ports or `data/` |
| `.agent/research.md` | RQs, invariants that must not break, terminology |
| `.agent/experiments.md` | configuration spec, file schemas, run order, safe sample handling |
| `.agent/rogueone.md` | positioning against RogueOne |
| `.agent/status.md` | what is done, frozen and still open |
| `latex:docs/` (`git show latex:docs/<file>`) | full design and decision log; when `.agent/` disagrees, `docs/` wins and `.agent/` gets fixed |

The manuscript, `docs/`, every PDF and the archived evaluation data live on the `latex` branch.
