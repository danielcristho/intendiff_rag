PY := $(shell [ -x .venv/bin/python ] && echo .venv/bin/python || echo python3)
# pipefail keeps a failed step visible behind `| tee`.
SHELL := bash
.SHELLFLAGS := -o pipefail -c

HF_CACHE ?= $(HOME)/.cache/huggingface
KB_FETCH ?= 600
HN_PATH_B_WANT ?= 60
# HOST runs a pipeline command that may reach the network; ISOLATED runs one with no network.
HOST = $(PY) -u -m pipeline
ISOLATED = docker run --rm --network none -u $$(id -u):$$(id -g) -v $(CURDIR):/work -w /work \
	-v $(HF_CACHE):/hf:ro -e HF_HUB_CACHE=/hf/hub -e HF_HUB_OFFLINE=1 intentdiff-analysis python -u -m pipeline

.PHONY: help venv install backend user-add ui test analysis-image data-mal data-typ data-pairs \
	data-dev kb-skeleton kb-promote hn-candidates hn-path-b hn-queue

help:
	@grep -hE '^[a-z-]+:.*?##' $(MAKEFILE_LIST) \
		| awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-9s\033[0m %s\n", $$1, $$2}'

venv: ## create .venv with the Python analysis dependencies
	python3 -m venv .venv && .venv/bin/pip install statsmodels matplotlib openpyxl pillow transformers

install: ## install frontend dependencies
	pnpm -C frontend install

# Both run from the repo root, where the backend finds .env and DATA_DIR.
backend: ## run the API with the settings in .env
	cargo run --manifest-path backend/Cargo.toml

user-add: ## create an annotator account or reset its password: make user-add NAME=daniel
	cargo run -q --manifest-path backend/Cargo.toml -- user-add $(NAME)

ui: ## run the audit UI
	pnpm -C frontend dev

test: ## run every suite
	cargo test --manifest-path backend/Cargo.toml
	pnpm -C frontend test
	$(PY) -m pipeline selfcheck

analysis-image: ## build the offline analysis image
	docker build -q -f deployments/docker/Dockerfile.analysis -t intentdiff-analysis .

data-mal: analysis-image ## unpack the Wyss package offline and build the MAL pairs
	$(ISOLATED) extract --plan pipeline/specs/wyss.plan.jsonl
	$(ISOLATED) pairs mal

data-typ: analysis-image ## draw the typical pairs on the host, then unpack and build them offline
	$(HOST) typical
	$(ISOLATED) extract --plan data/typ/extract.plan.jsonl
	$(ISOLATED) pairs typ

data-pairs: ## merge the pair subsets into data/pairs.jsonl
	$(HOST) pairs merge

data-dev: analysis-image ## draw the dev typical pairs on the host, then build the dev set offline
	$(HOST) devset draw
	$(ISOLATED) extract --plan data/typ/dev.extract.plan.jsonl
	$(ISOLATED) devset build

kb-skeleton: analysis-image ## fetch Datadog samples on the host, then select the cards offline
	$(HOST) kb fetch --count $(KB_FETCH)
	$(ISOLATED) extract --plan data/datadog/extract.plan.jsonl
	$(ISOLATED) kb select

kb-promote: analysis-image ## write data/kb.jsonl once every card is approved
	$(ISOLATED) kb-promote

hn-candidates: analysis-image ## HN path A: criteria and downloads on the host, delta offline
	$(HOST) hn-path-a prefilter 2>&1 | tee data/hn.log
	$(ISOLATED) extract --plan data/hn/extract.plan.jsonl 2>&1 | tee -a data/hn.log
	$(ISOLATED) hn-path-a screen 2>&1 | tee -a data/hn.log

hn-path-b: analysis-image ## HN path B for categories 1-4: fetch, match offline, verify
	for category in 1 2 3 4; do \
		$(HOST) hn-path-b fetch --category $$category && \
		$(ISOLATED) extract --plan data/hn/path-b/extract.plan.cat$$category.jsonl && \
		$(ISOLATED) hn-path-b match --category $$category && \
		$(HOST) hn-path-b verify --category $$category --want $(HN_PATH_B_WANT) || exit 1; \
	done 2>&1 | tee data/hn-path-b.log

hn-queue: analysis-image ## build the HN verification queue from path A and path B, offline
	$(ISOLATED) hn-queue

docker-up:
	docker compose up -d --build
	docker compose --profile model up -d vllm

docker-down:
	docker compose down
	docker compose --profile model down

docker-watch: ## rebuild and replace backend/frontend containers on every save
	docker compose up -d --build backend frontend
	docker compose watch backend frontend
