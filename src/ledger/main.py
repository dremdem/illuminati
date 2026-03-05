"""FastAPI application factory and entry point."""

import collections.abc
import contextlib
import os

import fastapi
import fastapi.middleware.cors as cors_middleware

import ledger.api.exception_handlers as exception_handlers
import ledger.api.routers.accounts as accounts_router
import ledger.api.routers.transactions as transactions_router
import ledger.infrastructure.database as database


@contextlib.asynccontextmanager
async def lifespan(
    app: fastapi.FastAPI,
) -> collections.abc.AsyncIterator[None]:
    """
    Manage application startup and shutdown: create engine and session factory.

    If DATABASE_URL is not set (e.g., unit tests), DB setup is skipped.

    :param app: FastAPI application instance
    """
    database_url = os.environ.get("DATABASE_URL")
    if database_url is not None:
        engine = database.create_async_engine(database_url)
        app.state.session_factory = database.create_async_session_factory(engine)
    yield
    if database_url is not None:
        await engine.dispose()


def create_app() -> fastapi.FastAPI:
    """
    Create and configure the FastAPI application instance.

    :return: configured FastAPI app with routers and middleware
    """
    app = fastapi.FastAPI(
        title="Financial Ledger API",
        description="Double-entry bookkeeping financial ledger system",
        version="0.1.0",
        lifespan=lifespan,
    )

    cors_origins = os.environ.get(
        "CORS_ORIGINS", "http://localhost:5173,http://localhost:3000"
    )
    app.add_middleware(
        cors_middleware.CORSMiddleware,
        allow_origins=[o.strip() for o in cors_origins.split(",") if o.strip()],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    exception_handlers.register_exception_handlers(app)
    app.include_router(accounts_router.router)
    app.include_router(transactions_router.router)
    app.include_router(transactions_router.account_transactions_router)

    @app.get(
        "/health",
        summary="Health check",
        description="Returns a simple status object indicating the service is running.",
        response_description="Status object with 'ok' value.",
    )
    async def health() -> dict[str, str]:
        """
        Health check endpoint.

        :return: status dict indicating the service is running
        """
        return {"status": "ok"}

    return app


app = create_app()
