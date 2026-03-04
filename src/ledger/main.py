"""FastAPI application factory and entry point."""

from fastapi import FastAPI


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application instance.

    :return: configured FastAPI app with routers and middleware
    """
    app = FastAPI(
        title="Financial Ledger API",
        description="Double-entry bookkeeping financial ledger system",
        version="0.1.0",
    )

    @app.get("/health")
    async def health() -> dict[str, str]:
        """
        Health check endpoint.

        :return: status dict indicating the service is running
        """
        return {"status": "ok"}

    return app


app = create_app()
