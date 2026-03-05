FROM python:3.11-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Install dependencies only (cache layer)
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-install-project

# Copy source and install the project itself
COPY src/ src/
COPY tests/ tests/
COPY alembic.ini ./
COPY alembic/ alembic/
RUN uv sync --frozen

FROM python:3.11-slim

WORKDIR /app

RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid 1000 --no-create-home appuser

COPY --from=builder --chown=appuser:appuser /app /app
COPY --chown=appuser:appuser entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh && chown appuser:appuser /app

ENV PATH="/app/.venv/bin:$PATH"

USER appuser

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["uvicorn", "ledger.main:app", "--host", "0.0.0.0", "--port", "8000"]
