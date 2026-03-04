"""FastAPI dependency injection functions for sessions, repositories, and services."""

import collections.abc
import typing

import fastapi
import sqlalchemy.ext.asyncio as sa_async

import ledger.application.account_service as account_service
import ledger.application.transaction_service as transaction_service
import ledger.infrastructure.repositories.account_repo as account_repo
import ledger.infrastructure.repositories.transaction_repo as transaction_repo


async def get_session(
    request: fastapi.Request,
) -> collections.abc.AsyncGenerator[sa_async.AsyncSession, None]:
    """
    Provide an async database session from the app-level session factory.

    Commits on success, rolls back on exception.

    :param request: current FastAPI request (carries app state)
    :return: yields an async session
    """
    session_factory: sa_async.async_sessionmaker[sa_async.AsyncSession] = (
        request.app.state.session_factory
    )
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_account_repository(
    session: typing.Annotated[sa_async.AsyncSession, fastapi.Depends(get_session)],
) -> account_repo.SqlaAccountRepository:
    """
    Build an account repository from the current session.

    :param session: async database session
    :return: account repository instance
    """
    return account_repo.SqlaAccountRepository(session)


def get_transaction_repository(
    session: typing.Annotated[sa_async.AsyncSession, fastapi.Depends(get_session)],
) -> transaction_repo.SqlaTransactionRepository:
    """
    Build a transaction repository from the current session.

    :param session: async database session
    :return: transaction repository instance
    """
    return transaction_repo.SqlaTransactionRepository(session)


def get_account_service(
    account_repository: typing.Annotated[
        account_repo.SqlaAccountRepository,
        fastapi.Depends(get_account_repository),
    ],
    transaction_repository: typing.Annotated[
        transaction_repo.SqlaTransactionRepository,
        fastapi.Depends(get_transaction_repository),
    ],
) -> account_service.AccountService:
    """
    Build an account service wired with repositories.

    :param account_repository: account repository instance
    :param transaction_repository: transaction repository instance
    :return: account service instance
    """
    return account_service.AccountService(
        account_repo=account_repository,
        transaction_repo=transaction_repository,
    )


def get_transaction_service(
    account_repository: typing.Annotated[
        account_repo.SqlaAccountRepository,
        fastapi.Depends(get_account_repository),
    ],
    transaction_repository: typing.Annotated[
        transaction_repo.SqlaTransactionRepository,
        fastapi.Depends(get_transaction_repository),
    ],
) -> transaction_service.TransactionService:
    """
    Build a transaction service wired with repositories.

    :param account_repository: account repository instance
    :param transaction_repository: transaction repository instance
    :return: transaction service instance
    """
    return transaction_service.TransactionService(
        account_repo=account_repository,
        transaction_repo=transaction_repository,
    )
