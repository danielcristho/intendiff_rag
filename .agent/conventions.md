# Conventions

How code, comments, tests and commits are written in this repository.

## Language

Everything inside a source file is **English**: comments, test names,
identifiers. `.agent/` is English too; the archived `docs/` on the `latex`
branch is Indonesian.
Code outlives the language its authors discussed it in.

## Writing code

- **One reason to change per file.** Extract past roughly 150 lines, or as soon
  as a file has a second audience. If a module needs "and" to describe it, split it.
- **Name things for what they are.** No `data`, `info`, `handle`, `manager`.
  If a comment is needed to explain a name, rename it.
- **Guard clauses first**, happy path unindented.
- **No speculative flexibility.** No parameter, interface, trait or config key
  with one caller and one value. No interface with a single implementation.
- **Data-driven over branching.** A new configuration is a new table entry
  (`pipeline/configs.py`, `pipeline/specs/`), not a new branch in five files.
- **DRY applies to knowledge, not characters.** Two functions that look alike
  but change for different reasons stay apart.
- **Prefer what is already here**: an existing helper, then the standard
  library, then an installed dependency. A new dependency needs a reason.

One rule is duplicated on purpose because it spans a language boundary:
`valid_annotator` in `backend/src/shared/files.rs` and `validAnnotator` in
`frontend/src/lib/annotator.ts` both encode `[A-Za-z0-9_-]{1,32}` and guard a
filename. **Change one, change the other**, and keep the test in each.

### Per stack

| Stack | Layout | Tooling |
|---|---|---|
| Python (`pipeline/`, `scripts/`) | one module per step, `--selfcheck` flag for its check | `make venv` (uv); add a dependency with `uv add <pkg>==<version>`, commit `pyproject.toml` and `uv.lock` together |
| Rust (`backend/`) | `src/modules/<feature>/{routes,handlers,dto,repository}.rs`; shared helpers in `src/shared/` | `cargo fmt`, `cargo test` |
| TypeScript (`frontend/`) | structure follows `.ref/spider/frontend`, design tokens follow `.ref/cloudx_ui` | `pnpm test`, `pnpm build` |

## Comments

Based on Stack Overflow's "Best practices for writing code comments"
(2021-12-23).

1. **Never duplicate the code.** `# sha256_text returns a hex digest` above
   `def sha256_text` is noise; delete it.
2. **A comment never excuses unclear code.** Rename or restructure instead.
3. **If the comment is hard to write, the code is probably wrong.**
4. **Dispel confusion, do not add it.**
5. **Explain unidiomatic code.** A trade-off, a constraint, a trap someone would
   otherwise reintroduce. This is where comments earn their keep.
6. **Link the source of copied code.**
7. **Link an external reference only when the code cannot be read without it**
   (a file-format spec, a copied algorithm). Never narrate the research: no RQ
   numbers, no hypotheses, no "why the study needs this". The design lives in `.agent/`.
8. **Comment when fixing a bug**, saying what broke.
9. **Mark incomplete work.** `TODO` for a gap; `ponytail:` for a deliberate
   shortcut, naming its ceiling and upgrade path; `SAFETY:` on every Rust
   `unsafe` block.

Format:

- **One or two lines.** A paragraph in a source file belongs in `.agent/`.
- **Module docstrings say how to run the file**, nothing more.
- A comment on a declaration **starts with the declaration's own name**
  (`// write_atomic renames ...`, never `// Writes ...`). That is the format for
  comments worth writing, not a reason to write one everywhere.

## Tests

- Non-trivial logic leaves **one runnable check**: a Rust `#[cfg(test)]` module
  or a file in `backend/tests/`, a Vitest file, a `--selfcheck` flag, or a
  `tests/test_*.py` file.
- **Name a test after the invariant it pins**, not the function it calls:
  `keeps_two_annotators_verdicts_on_the_same_pair_apart`, not `test_merge`.
- New checks are wired into `make test`. `make test` must pass before a push.
- Test fixtures use made-up names (`alice`, `bob`, `pkg-a`), never real people
  or hosts.

## Commits

[Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/):

```
<type>(<scope>): <subject>

<body: why, and what broke if it is a fix>

Co-Authored-By: ...   (only when an agent wrote the change)
```

- **type**: `feat`, `fix`, `refactor`, `test`, `docs`, `build`, `chore`.
  Prompt, configuration, capability-list or decision-rule changes are `feat` or
  `fix` and need a decision entry: add it to `docs/decisions.md` on the
  `latex` branch and name the decision (`D<n>`) in the commit body (G2 rule).
- **scope**: the top-level area, `pipeline`, `backend`, `frontend`, `data`,
  `docs`, `compose`, `deploy`. Leave it out when the change spans several.
- **subject**: English, imperative, lowercase, no trailing full stop, at most
  72 characters. Say what changes in behaviour, not which files moved:
  `fix(pipeline): retry connection resets, which bypassed the backoff`.
- **One logical change per commit, one subject per commit.** Never paste several
  subjects into one line (`feat(a): x feat(b): y`); make several commits.
- **Body** explains why. Wrap at 72 columns. Reference a decision as `D<n>`.
- Never commit secrets (`.env`, `data/users.json`), downloaded samples
  (`data/wyss/`, `data/typ/`, `data/hn/`, `data/tarballs/`), PDFs or LaTeX
  build output. Stage paths explicitly; do not `git add -A` at the root.
- No host names, IP addresses, home-directory paths or personal names in code,
  docs or commit messages. Use `<gpu-host>`, `<host-ip-address>`, paths
  relative to the repository root.

## Branches

- `main`: code, `.agent/` and the data the code reads.
- `latex`: the manuscript (`labs/latex/`), the design documents and decision
  log (`docs/`), every PDF, `scratchpad/` and the evaluation data no code reads
  any more.
- Work on a short-lived branch and merge through a pull request. Merging an
  older branch into `main` must not take "theirs" wholesale: the merge that
  reverted the modular backend (`refactor(backend)` restored it) did exactly that.
