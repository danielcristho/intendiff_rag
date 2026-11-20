PORT ?= 8100
DATA ?= ./data
# The pipeline's dependencies live in .venv (`make venv`); a system python lacks them.
PY :=$(shell [ -x .venv/bin/python ] && echo .venv/bin/python || echo python3)

.PHONY: help venv install backend ui test

help:
	@grep -hE '^[a-z-]+:.*?##' $(MAKEFILE_LIST) \
		| awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-9s\033[0m %s\n", $$1, $$2}'

venv: ## create .venv from uv.lock
	uv sync --frozen

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
