# 8000 is taken by production-service on the GPU host; stay clear of it.
PORT ?= 8100
DATA ?= ./data

.PHONY: help install backend ui test

help:
	@grep -hE '^[a-z-]+:.*?##' $(MAKEFILE_LIST) \
		| awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-9s\033[0m %s\n", $$1, $$2}'

install:
	pnpm -C frontend install

backend:
	cd backend && cargo run -- --data-dir ../$(DATA) --port $(PORT)

ui:
	pnpm -C frontend dev

test:
	cargo test --manifest-path backend/Cargo.toml
	pnpm -C frontend test
	python3 pipeline/runner.py --selfcheck
