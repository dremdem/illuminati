.PHONY: up down build lint typecheck test check run seed-data \
       db-reset db-migrate db-revision db-shell db-dump db-restore

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

# ── Database management ──────────────────────────────────────────────

db-reset:
	@echo "WARNING: This will delete ALL data in the database."
	@read -p "Type 'yes' to confirm: " confirm && [ "$$confirm" = "yes" ] || (echo "Aborted." && exit 1)
	docker compose run --rm app alembic downgrade base
	docker compose run --rm app alembic upgrade head
	@echo "Database reset complete."

db-migrate:
	docker compose run --rm app alembic upgrade head

db-revision:
	docker compose run --rm app alembic revision --autogenerate -m "$(msg)"

db-shell:
	docker compose exec db psql -U ledger -d ledger

db-dump:
	docker compose exec db pg_dump -U ledger ledger > dump_$$(date +%Y%m%d_%H%M%S).sql
	@echo "Dump saved to dump_$$(date +%Y%m%d_%H%M%S).sql"

db-restore:
	docker compose exec -T db psql -U ledger -d ledger < $(file)
