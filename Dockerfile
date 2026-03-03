FROM python:3.11-slim AS base

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Install dependencies first (cache layer)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

# Copy source code
COPY src/ src/
COPY tests/ tests/
COPY alembic.ini ./
COPY alembic/ alembic/

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

CMD ["uvicorn", "ledger.main:app", "--host", "0.0.0.0", "--port", "8000"]
