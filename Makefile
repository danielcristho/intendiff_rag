PORT ?= 8100
DATA ?= ./data
# analysis.py needs statsmodels (D43) and plots.py needs matplotlib, neither of
# which a system python is allowed to install under PEP 668.
PY := $(shell [ -x .venv/bin/python ] && echo .venv/bin/python || echo python3)

.PHONY: help venv install backend ui test

help:
	@grep -hE '^[a-z-]+:.*?##' $(MAKEFILE_LIST) \
		| awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-9s\033[0m %s\n", $$1, $$2}'

venv: ## create .venv with the Python analysis dependencies
	# uv first: a Debian python without the python3-venv package has no ensurepip,
	# and there `python3 -m venv` cannot bootstrap pip at all.
	@if command -v uv >/dev/null; then \
		uv venv .venv && uv pip install --python .venv/bin/python statsmodels matplotlib; \
	else \
		python3 -m venv .venv && .venv/bin/pip install statsmodels matplotlib; \
	fi

install: ## install frontend dependencies
	pnpm -C frontend install

backend: ## run the API on $(PORT)
	cd backend && cargo run -- --data-dir ../$(DATA) --port $(PORT)

ui: ## run the audit UI
	pnpm -C frontend dev

test: ## run every suite
	cargo test --manifest-path backend/Cargo.toml
	pnpm -C frontend test
	$(PY) pipeline/configs.py --selfcheck
	$(PY) pipeline/runner.py --selfcheck
	$(PY) pipeline/sampling_grid.py --selfcheck
	$(PY) pipeline/sampling_report.py --selfcheck
	$(PY) pipeline/test_runner_inputs.py
	$(PY) pipeline/capability.py --selfcheck
	$(PY) pipeline/prompts.py
	$(PY) pipeline/collect.py --selfcheck
	$(PY) pipeline/samples.py --selfcheck
	$(PY) pipeline/archives.py --selfcheck
	$(PY) pipeline/wyss.py --selfcheck
	$(PY) pipeline/registry_fetch.py --selfcheck
	$(PY) pipeline/advisories.py --selfcheck
	$(PY) pipeline/typical.py --selfcheck
	$(PY) pipeline/kb.py --selfcheck
	$(PY) pipeline/hardnegative.py --selfcheck
	$(PY) pipeline/smartdiff.py --selfcheck
	$(PY) pipeline/normalization.py --selfcheck
	$(PY) pipeline/intent.py --selfcheck
	$(PY) pipeline/dataset.py --selfcheck
	$(PY) pipeline/campaign.py --selfcheck
	$(PY) pipeline/analysis.py --selfcheck
	$(PY) pipeline/plots.py --selfcheck

docker-up:
	docker compose up -d --build

docker-down:
	docker compose down
