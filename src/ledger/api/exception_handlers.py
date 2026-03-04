"""Map domain exceptions to HTTP error responses."""

import fastapi
import fastapi.responses

import ledger.domain.exceptions as exceptions


async def account_not_found_handler(
    request: fastapi.Request,
    exc: exceptions.AccountNotFoundError,
) -> fastapi.responses.JSONResponse:
    """
    Handle AccountNotFoundError with a 404 response.

    :param request: current request
    :param exc: the raised exception
    :return: JSON response with 404 status
    """
    return fastapi.responses.JSONResponse(
        status_code=404,
        content={"detail": str(exc)},
    )


async def duplicate_account_handler(
    request: fastapi.Request,
    exc: exceptions.DuplicateAccountError,
) -> fastapi.responses.JSONResponse:
    """
    Handle DuplicateAccountError with a 409 response.

    :param request: current request
    :param exc: the raised exception
    :return: JSON response with 409 status
    """
    return fastapi.responses.JSONResponse(
        status_code=409,
        content={"detail": str(exc)},
    )


async def transaction_not_found_handler(
    request: fastapi.Request,
    exc: exceptions.TransactionNotFoundError,
) -> fastapi.responses.JSONResponse:
    """
    Handle TransactionNotFoundError with a 404 response.

    :param request: current request
    :param exc: the raised exception
    :return: JSON response with 404 status
    """
    return fastapi.responses.JSONResponse(
        status_code=404,
        content={"detail": str(exc)},
    )


async def domain_error_handler(
    request: fastapi.Request,
    exc: exceptions.DomainError,
) -> fastapi.responses.JSONResponse:
    """
    Handle generic DomainError with a 400 response (catch-all).

    :param request: current request
    :param exc: the raised exception
    :return: JSON response with 400 status
    """
    return fastapi.responses.JSONResponse(
        status_code=400,
        content={"detail": str(exc)},
    )


def register_exception_handlers(app: fastapi.FastAPI) -> None:
    """
    Register domain exception handlers on the FastAPI app.

    More specific exceptions are registered first; FastAPI matches
    using isinstance(), so order matters.

    :param app: FastAPI application instance
    """
    app.add_exception_handler(
        exceptions.AccountNotFoundError,
        account_not_found_handler,  # type: ignore[arg-type]
    )
    app.add_exception_handler(
        exceptions.DuplicateAccountError,
        duplicate_account_handler,  # type: ignore[arg-type]
    )
    app.add_exception_handler(
        exceptions.TransactionNotFoundError,
        transaction_not_found_handler,  # type: ignore[arg-type]
    )
    app.add_exception_handler(
        exceptions.DomainError,
        domain_error_handler,  # type: ignore[arg-type]
    )
