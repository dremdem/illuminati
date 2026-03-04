"""Integration tests for SqlaTransactionRepository against real PostgreSQL."""

import datetime
import decimal
import uuid

import pytest
import sqlalchemy.ext.asyncio as sa_async

import ledger.domain.enums as enums
import ledger.domain.models as models
import ledger.infrastructure.repositories.account_repo as account_repo_mod
import ledger.infrastructure.repositories.transaction_repo as txn_repo_mod


@pytest.fixture
async def two_accounts(
    db_session: sa_async.AsyncSession,
) -> tuple[models.Account, models.Account]:
    """
    Create two accounts (Cash ASSET, Revenue REVENUE) for transaction tests.

    :param db_session: per-test async session
    :return: tuple of (cash_account, revenue_account)
    """
    repo = account_repo_mod.SqlaAccountRepository(db_session)
    cash = await repo.create(
        models.Account(id=uuid.uuid4(), name="Cash", type=enums.AccountType.ASSET)
    )
    revenue = await repo.create(
        models.Account(id=uuid.uuid4(), name="Revenue", type=enums.AccountType.REVENUE)
    )
    return cash, revenue


def _make_transaction(cash_id: uuid.UUID, revenue_id: uuid.UUID) -> models.Transaction:
    """
    Build a balanced domain transaction between two accounts.

    :param cash_id: UUID of the debit account
    :param revenue_id: UUID of the credit account
    :return: domain transaction with two entries
    """
    txn_id = uuid.uuid4()
    return models.Transaction(
        id=txn_id,
        timestamp=datetime.datetime.now(tz=datetime.UTC),
        description="Sale",
        entries=[
            models.TransactionEntry(
                id=uuid.uuid4(),
                transaction_id=txn_id,
                account_id=cash_id,
                type=enums.EntryType.DEBIT,
                amount=decimal.Decimal("100.00"),
            ),
            models.TransactionEntry(
                id=uuid.uuid4(),
                transaction_id=txn_id,
                account_id=revenue_id,
                type=enums.EntryType.CREDIT,
                amount=decimal.Decimal("100.00"),
            ),
        ],
    )


class TestTransactionRepoCreate:
    """Tests for SqlaTransactionRepository.create()."""

    async def test_create_persists_transaction(
        self,
        db_session: sa_async.AsyncSession,
        two_accounts: tuple[models.Account, models.Account],
    ) -> None:
        """Create persists a transaction with its entries."""
        cash, revenue = two_accounts
        repo = txn_repo_mod.SqlaTransactionRepository(db_session)
        txn = _make_transaction(cash.id, revenue.id)

        result = await repo.create(txn)

        assert result.id == txn.id
        assert result.description == "Sale"
        assert len(result.entries) == 2

    async def test_create_preserves_entry_fields(
        self,
        db_session: sa_async.AsyncSession,
        two_accounts: tuple[models.Account, models.Account],
    ) -> None:
        """Create round-trips all entry fields correctly."""
        cash, revenue = two_accounts
        repo = txn_repo_mod.SqlaTransactionRepository(db_session)
        txn = _make_transaction(cash.id, revenue.id)

        result = await repo.create(txn)

        debit = next(e for e in result.entries if e.type == enums.EntryType.DEBIT)
        credit = next(e for e in result.entries if e.type == enums.EntryType.CREDIT)
        assert debit.account_id == cash.id
        assert debit.amount == decimal.Decimal("100.00")
        assert credit.account_id == revenue.id
        assert credit.amount == decimal.Decimal("100.00")


class TestTransactionRepoGetById:
    """Tests for SqlaTransactionRepository.get_by_id()."""

    async def test_get_by_id_found(
        self,
        db_session: sa_async.AsyncSession,
        two_accounts: tuple[models.Account, models.Account],
    ) -> None:
        """get_by_id returns the transaction with all entries."""
        cash, revenue = two_accounts
        repo = txn_repo_mod.SqlaTransactionRepository(db_session)
        txn = _make_transaction(cash.id, revenue.id)
        await repo.create(txn)

        result = await repo.get_by_id(txn.id)

        assert result is not None
        assert result.id == txn.id
        assert result.description == "Sale"
        assert len(result.entries) == 2

    async def test_get_by_id_not_found(
        self,
        db_session: sa_async.AsyncSession,
    ) -> None:
        """get_by_id returns None for a non-existent transaction."""
        repo = txn_repo_mod.SqlaTransactionRepository(db_session)

        result = await repo.get_by_id(uuid.uuid4())

        assert result is None


class TestTransactionRepoGetByAccountId:
    """Tests for SqlaTransactionRepository.get_by_account_id()."""

    async def test_get_by_account_id_returns_matching(
        self,
        db_session: sa_async.AsyncSession,
        two_accounts: tuple[models.Account, models.Account],
    ) -> None:
        """get_by_account_id returns transactions involving the given account."""
        cash, revenue = two_accounts
        repo = txn_repo_mod.SqlaTransactionRepository(db_session)
        txn = _make_transaction(cash.id, revenue.id)
        await repo.create(txn)

        result = await repo.get_by_account_id(cash.id)

        assert len(result) == 1
        assert result[0].id == txn.id

    async def test_get_by_account_id_preserves_all_entries(
        self,
        db_session: sa_async.AsyncSession,
        two_accounts: tuple[models.Account, models.Account],
    ) -> None:
        """get_by_account_id returns full transactions with ALL entries."""
        cash, revenue = two_accounts
        repo = txn_repo_mod.SqlaTransactionRepository(db_session)
        txn = _make_transaction(cash.id, revenue.id)
        await repo.create(txn)

        result = await repo.get_by_account_id(cash.id)

        assert len(result[0].entries) == 2

    async def test_get_by_account_id_empty(
        self,
        db_session: sa_async.AsyncSession,
    ) -> None:
        """get_by_account_id returns empty list for an account with no transactions."""
        repo = txn_repo_mod.SqlaTransactionRepository(db_session)

        result = await repo.get_by_account_id(uuid.uuid4())

        assert result == []
