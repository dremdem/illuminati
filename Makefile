.PHONY: up down build lint typecheck test check run seed-data

up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build

lint:
	docker compose run --rm --no-deps app ruff check .
	docker compose run --rm --no-deps app ruff format --check .

format:
	docker compose run --rm --no-deps app ruff format .

typecheck:
	docker compose run --rm --no-deps app mypy src/

test:
	docker compose run --rm --user root app pytest -v

check: lint typecheck test

run:
	docker compose run --rm --no-deps app uvicorn ledger.main:app --host 0.0.0.0 --port 8000

seed-data:
	docker compose run --rm app python -m ledger.scripts.seed
