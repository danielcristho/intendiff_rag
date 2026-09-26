PORT ?= 8100
DATA ?= ./data
PY := $(shell [ -x .venv/bin/python ] && echo .venv/bin/python || echo python3)

.PHONY: help venv install backend ui test

help:
	@grep -hE '^[a-z-]+:.*?##' $(MAKEFILE_LIST) \
		| awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-9s\033[0m %s\n", $$1, $$2}'

venv: ## create .venv with the Python analysis dependencies
	python3 -m venv .venv && .venv/bin/pip install statsmodels matplotlib openpyxl pillow transformers

install: ## install frontend dependencies
	pnpm -C frontend install

backend: ## run the API on $(PORT)
	cd backend && cargo run -- --data-dir ../$(DATA) --port $(PORT)

ui: ## run the audit UI
	pnpm -C frontend dev

test: ## run every suite
	cargo test --manifest-path backend/Cargo.toml
	pnpm -C frontend test
	$(PY) pipeline/runner.py --selfcheck
	$(PY) pipeline/capability.py --selfcheck
	$(PY) pipeline/prompts.py
	$(PY) pipeline/collect.py --selfcheck
	$(PY) pipeline/smartdiff.py --selfcheck
	$(PY) pipeline/intent.py --selfcheck
	$(PY) pipeline/campaign.py --selfcheck
	$(PY) pipeline/pairs.py --selfcheck
	$(PY) pipeline/kb.py --selfcheck
	$(PY) pipeline/devset.py --selfcheck
	$(PY) pipeline/promote.py --selfcheck
	$(PY) pipeline/analysis.py --selfcheck
	$(PY) pipeline/plots.py --selfcheck
	$(PY) pipeline/tables.py --selfcheck

docker-up:
	docker compose up -d --build

docker-down:
	docker compose down

docker-watch: ## rebuild and replace backend/frontend containers on every save
	docker compose up -d --build backend frontend
	docker compose watch backend frontend
