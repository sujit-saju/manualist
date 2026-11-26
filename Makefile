.PHONY: up down setup test lint fmt gen-api

up:
	docker compose up --build

down:
	docker compose down

setup:
	cd Server && uv sync --locked
	cd UI && pnpm install --frozen-lockfile

test:
	cd Server && uv run --locked pytest --cov=src.services --cov-fail-under=80
	cd UI && pnpm test

lint:
	cd Server && uv run --locked ruff check . && uv run --locked ruff format --check . && uv run --locked mypy src tests
	cd UI && pnpm lint && pnpm typecheck && pnpm exec prettier --check .

fmt:
	cd Server && uv run --locked ruff check --fix . && uv run --locked ruff format .
	cd UI && pnpm fmt

gen-api:
	cd Server && uv run --locked python -m src.api.export_openapi
	cd UI && pnpm gen:api
