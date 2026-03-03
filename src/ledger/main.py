from fastapi import FastAPI


def create_app() -> FastAPI:
    app = FastAPI(
        title="Financial Ledger API",
        description="Double-entry bookkeeping financial ledger system",
        version="0.1.0",
    )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
