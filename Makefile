.PHONY: up down build lint typecheck test check run seed-data \
       db-reset db-migrate db-revision db-shell db-dump db-restore \
       frontend-dev frontend-build frontend-install help

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}' | sort

up: ## Start all services in the background
	docker compose up -d

down: ## Stop all services
	docker compose down

build: ## Build Docker images
	docker compose build

lint: ## Run linter and format checks
	docker compose run --rm --no-deps app ruff check .
	docker compose run --rm --no-deps app ruff format --check .

format: ## Auto-format source code
	docker compose run --rm --no-deps app ruff format .

typecheck: ## Run static type checks
	docker compose run --rm --no-deps app mypy src/

test: ## Run the test suite
	docker compose run --rm --user root app pytest -v

check: lint typecheck test ## Run lint, typecheck, and tests

run: ## Run the API server locally
	docker compose run --rm --no-deps app uvicorn ledger.main:app --host 0.0.0.0 --port 8000

seed-data: ## Seed the database with sample data
	docker compose run --rm app python -m ledger.scripts.seed

# ── Database management ──────────────────────────────────────────────

db-reset: ## Reset the database (drops and re-applies all migrations)
	@echo "WARNING: This will delete ALL data in the database."
	@read -p "Type 'yes' to confirm: " confirm && [ "$$confirm" = "yes" ] || (echo "Aborted." && exit 1)
	docker compose run --rm app alembic downgrade base
	docker compose run --rm app alembic upgrade head
	@echo "Database reset complete."

db-migrate: ## Apply pending database migrations
	docker compose run --rm app alembic upgrade head

db-revision: ## Generate a new migration (usage: make db-revision msg="description")
	docker compose run --rm app alembic revision --autogenerate -m "$(msg)"

db-shell: ## Open a psql shell to the database
	docker compose exec db psql -U ledger -d ledger

db-dump: ## Dump the database to a SQL file
	docker compose exec db pg_dump -U ledger ledger > dump_$$(date +%Y%m%d_%H%M%S).sql
	@echo "Dump saved to dump_$$(date +%Y%m%d_%H%M%S).sql"

db-restore: ## Restore the database from a SQL file (usage: make db-restore file=<path>)
	docker compose exec -T db psql -U ledger -d ledger < $(file)

# ── Frontend ─────────────────────────────────────────────────────────

frontend-install: ## Install frontend npm dependencies
	cd frontend && npm install

frontend-dev: ## Start the frontend dev server
	cd frontend && npm run dev

frontend-build: ## Build the frontend for production
	cd frontend && npm run build
