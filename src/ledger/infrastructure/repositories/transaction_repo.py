"""SQLAlchemy-based transaction repository implementation."""

import uuid

import sqlalchemy as sa
import sqlalchemy.ext.asyncio as sa_async

import ledger.domain.models as models
import ledger.infrastructure.mappers as mappers
import ledger.infrastructure.models as orm_models


class SqlaTransactionRepository:
    """Transaction repository backed by SQLAlchemy async sessions."""

    def __init__(self, session: sa_async.AsyncSession) -> None:
        """
        Initialise the repository with a database session.

        :param session: async SQLAlchemy session
        """
        self._session = session

    async def create(self, transaction: models.Transaction) -> models.Transaction:
        """
        Persist a new transaction with its entries.

        :param transaction: domain transaction to persist
        :return: the persisted transaction
        """
        orm_txn = mappers.transaction_to_orm(transaction)
        self._session.add(orm_txn)
        await self._session.flush()
        return mappers.transaction_to_domain(orm_txn)

    async def get_by_id(self, transaction_id: uuid.UUID) -> models.Transaction | None:
        """
        Retrieve a transaction by its unique identifier.

        Entries are auto-loaded via selectin lazy loading.

        :param transaction_id: UUID of the transaction
        :return: the transaction with entries, or None if not found
        """
        row = await self._session.get(orm_models.TransactionModel, transaction_id)
        if row is None:
            return None
        else:
            return mappers.transaction_to_domain(row)

    async def get_by_account_id(
        self, account_id: uuid.UUID
    ) -> list[models.Transaction]:
        """
        Retrieve all transactions that have at least one entry for the given account.

        Uses a join with DISTINCT to find matching transactions, then returns
        full transactions with ALL entries (preserving double-entry invariant).

        :param account_id: UUID of the account
        :return: list of transactions involving the account
        """
        stmt = (
            sa.select(orm_models.TransactionModel)
            .join(orm_models.TransactionEntryModel)
            .where(orm_models.TransactionEntryModel.account_id == account_id)
            .distinct()
        )
        result = await self._session.execute(stmt)
        rows = result.scalars().all()
        return [mappers.transaction_to_domain(r) for r in rows]
