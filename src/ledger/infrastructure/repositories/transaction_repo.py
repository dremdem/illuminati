"""SQLAlchemy-based transaction repository implementation."""

import datetime
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
        self,
        account_id: uuid.UUID,
        limit: int | None = None,
        offset: int = 0,
        from_date: datetime.datetime | None = None,
        to_date: datetime.datetime | None = None,
    ) -> tuple[list[models.Transaction], int]:
        """
        Retrieve transactions that have at least one entry for the given account.

        Uses a join with DISTINCT to find matching transactions, then returns
        full transactions with ALL entries (preserving double-entry invariant).

        :param account_id: UUID of the account
        :param limit: maximum number of transactions to return (None = all)
        :param offset: number of transactions to skip
        :param from_date: inclusive lower bound on transaction timestamp
        :param to_date: inclusive upper bound on transaction timestamp
        :return: tuple of (list of transactions, total count)
        """
        count_stmt = (
            sa.select(sa.func.count(sa.distinct(orm_models.TransactionModel.id)))
            .join(orm_models.TransactionEntryModel)
            .where(orm_models.TransactionEntryModel.account_id == account_id)
        )
        if from_date is not None:
            count_stmt = count_stmt.where(
                orm_models.TransactionModel.timestamp >= from_date
            )
        if to_date is not None:
            count_stmt = count_stmt.where(
                orm_models.TransactionModel.timestamp <= to_date
            )
        count_result = await self._session.execute(count_stmt)
        total = count_result.scalar_one()

        stmt = (
            sa.select(orm_models.TransactionModel)
            .join(orm_models.TransactionEntryModel)
            .where(orm_models.TransactionEntryModel.account_id == account_id)
        )
        if from_date is not None:
            stmt = stmt.where(orm_models.TransactionModel.timestamp >= from_date)
        if to_date is not None:
            stmt = stmt.where(orm_models.TransactionModel.timestamp <= to_date)
        stmt = (
            stmt.distinct()
            .order_by(orm_models.TransactionModel.timestamp)
            .offset(offset)
        )
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self._session.execute(stmt)
        rows = result.scalars().all()
        return [mappers.transaction_to_domain(r) for r in rows], total

    async def get_all(
        self,
        limit: int | None = None,
        offset: int = 0,
        from_date: datetime.datetime | None = None,
        to_date: datetime.datetime | None = None,
    ) -> tuple[list[models.Transaction], int]:
        """
        Retrieve all transactions with optional pagination and date filtering.

        :param limit: maximum number of transactions to return (None = all)
        :param offset: number of transactions to skip
        :param from_date: inclusive lower bound on transaction timestamp
        :param to_date: inclusive upper bound on transaction timestamp
        :return: tuple of (list of transactions, total count)
        """
        count_stmt = sa.select(sa.func.count()).select_from(orm_models.TransactionModel)
        if from_date is not None:
            count_stmt = count_stmt.where(
                orm_models.TransactionModel.timestamp >= from_date
            )
        if to_date is not None:
            count_stmt = count_stmt.where(
                orm_models.TransactionModel.timestamp <= to_date
            )
        count_result = await self._session.execute(count_stmt)
        total = count_result.scalar_one()

        stmt = sa.select(orm_models.TransactionModel)
        if from_date is not None:
            stmt = stmt.where(orm_models.TransactionModel.timestamp >= from_date)
        if to_date is not None:
            stmt = stmt.where(orm_models.TransactionModel.timestamp <= to_date)
        stmt = stmt.order_by(orm_models.TransactionModel.timestamp).offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self._session.execute(stmt)
        rows = result.scalars().all()
        return [mappers.transaction_to_domain(r) for r in rows], total
