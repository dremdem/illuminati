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


def _make_transaction_with_timestamp(
    cash_id: uuid.UUID,
    revenue_id: uuid.UUID,
    timestamp: datetime.datetime,
    description: str = "Sale",
) -> models.Transaction:
    """
    Build a balanced domain transaction with a specific timestamp.

    :param cash_id: UUID of the debit account
    :param revenue_id: UUID of the credit account
    :param timestamp: when the transaction occurred
    :param description: human-readable description
    :return: domain transaction with two entries
    """
    txn_id = uuid.uuid4()
    return models.Transaction(
        id=txn_id,
        timestamp=timestamp,
        description=description,
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

        items, total = await repo.get_by_account_id(cash.id)

        assert len(items) == 1
        assert items[0].id == txn.id
        assert total == 1

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

        items, total = await repo.get_by_account_id(cash.id)

        assert len(items[0].entries) == 2
        assert total == 1

    async def test_get_by_account_id_empty(
        self,
        db_session: sa_async.AsyncSession,
    ) -> None:
        """get_by_account_id returns empty list for an account with no transactions."""
        repo = txn_repo_mod.SqlaTransactionRepository(db_session)

        items, total = await repo.get_by_account_id(uuid.uuid4())

        assert items == []
        assert total == 0


class TestTransactionRepoPaginationAndFiltering:
    """Tests for get_by_account_id() pagination and date filtering."""

    async def test_limit_restricts_result_count(
        self,
        db_session: sa_async.AsyncSession,
        two_accounts: tuple[models.Account, models.Account],
    ) -> None:
        """get_by_account_id with limit=1 returns at most 1 transaction."""
        cash, revenue = two_accounts
        repo = txn_repo_mod.SqlaTransactionRepository(db_session)
        for i in range(3):
            txn = _make_transaction_with_timestamp(
                cash.id,
                revenue.id,
                datetime.datetime(2025, 1, i + 1, tzinfo=datetime.UTC),
                description=f"Sale {i + 1}",
            )
            await repo.create(txn)

        items, total = await repo.get_by_account_id(cash.id, limit=1)

        assert len(items) == 1
        assert total == 3

    async def test_offset_skips_rows(
        self,
        db_session: sa_async.AsyncSession,
        two_accounts: tuple[models.Account, models.Account],
    ) -> None:
        """get_by_account_id with offset=1 skips the first transaction."""
        cash, revenue = two_accounts
        repo = txn_repo_mod.SqlaTransactionRepository(db_session)
        for i in range(3):
            txn = _make_transaction_with_timestamp(
                cash.id,
                revenue.id,
                datetime.datetime(2025, 1, i + 1, tzinfo=datetime.UTC),
                description=f"Sale {i + 1}",
            )
            await repo.create(txn)

        items, total = await repo.get_by_account_id(cash.id, offset=1)

        assert len(items) == 2
        assert total == 3

    async def test_from_date_filters_transactions(
        self,
        db_session: sa_async.AsyncSession,
        two_accounts: tuple[models.Account, models.Account],
    ) -> None:
        """get_by_account_id with from_date excludes earlier transactions."""
        cash, revenue = two_accounts
        repo = txn_repo_mod.SqlaTransactionRepository(db_session)
        for i in range(3):
            txn = _make_transaction_with_timestamp(
                cash.id,
                revenue.id,
                datetime.datetime(2025, 1, i + 1, tzinfo=datetime.UTC),
                description=f"Sale {i + 1}",
            )
            await repo.create(txn)

        items, total = await repo.get_by_account_id(
            cash.id,
            from_date=datetime.datetime(2025, 1, 2, tzinfo=datetime.UTC),
        )

        assert len(items) == 2
        descriptions = {t.description for t in items}
        assert "Sale 1" not in descriptions
        assert total == 2

    async def test_to_date_filters_transactions(
        self,
        db_session: sa_async.AsyncSession,
        two_accounts: tuple[models.Account, models.Account],
    ) -> None:
        """get_by_account_id with to_date excludes later transactions."""
        cash, revenue = two_accounts
        repo = txn_repo_mod.SqlaTransactionRepository(db_session)
        for i in range(3):
            txn = _make_transaction_with_timestamp(
                cash.id,
                revenue.id,
                datetime.datetime(2025, 1, i + 1, tzinfo=datetime.UTC),
                description=f"Sale {i + 1}",
            )
            await repo.create(txn)

        items, total = await repo.get_by_account_id(
            cash.id,
            to_date=datetime.datetime(2025, 1, 2, tzinfo=datetime.UTC),
        )

        assert len(items) == 2
        descriptions = {t.description for t in items}
        assert "Sale 3" not in descriptions
        assert total == 2

    async def test_date_range_filters_transactions(
        self,
        db_session: sa_async.AsyncSession,
        two_accounts: tuple[models.Account, models.Account],
    ) -> None:
        """from_date + to_date returns only transactions in range."""
        cash, revenue = two_accounts
        repo = txn_repo_mod.SqlaTransactionRepository(db_session)
        for i in range(5):
            txn = _make_transaction_with_timestamp(
                cash.id,
                revenue.id,
                datetime.datetime(2025, 1, i + 1, tzinfo=datetime.UTC),
                description=f"Sale {i + 1}",
            )
            await repo.create(txn)

        items, total = await repo.get_by_account_id(
            cash.id,
            from_date=datetime.datetime(2025, 1, 2, tzinfo=datetime.UTC),
            to_date=datetime.datetime(2025, 1, 4, tzinfo=datetime.UTC),
        )

        assert len(items) == 3
        descriptions = {t.description for t in items}
        assert descriptions == {"Sale 2", "Sale 3", "Sale 4"}
        assert total == 3

    async def test_no_limit_returns_all(
        self,
        db_session: sa_async.AsyncSession,
        two_accounts: tuple[models.Account, models.Account],
    ) -> None:
        """get_by_account_id without limit returns all transactions."""
        cash, revenue = two_accounts
        repo = txn_repo_mod.SqlaTransactionRepository(db_session)
        for i in range(3):
            txn = _make_transaction_with_timestamp(
                cash.id,
                revenue.id,
                datetime.datetime(2025, 1, i + 1, tzinfo=datetime.UTC),
                description=f"Sale {i + 1}",
            )
            await repo.create(txn)

        items, total = await repo.get_by_account_id(cash.id)

        assert len(items) == 3
        assert total == 3

    async def test_total_reflects_filtered_count(
        self,
        db_session: sa_async.AsyncSession,
        two_accounts: tuple[models.Account, models.Account],
    ) -> None:
        """total reflects count after date filters but before limit/offset."""
        cash, revenue = two_accounts
        repo = txn_repo_mod.SqlaTransactionRepository(db_session)
        for i in range(5):
            txn = _make_transaction_with_timestamp(
                cash.id,
                revenue.id,
                datetime.datetime(2025, 1, i + 1, tzinfo=datetime.UTC),
                description=f"Sale {i + 1}",
            )
            await repo.create(txn)

        items, total = await repo.get_by_account_id(
            cash.id,
            limit=1,
            from_date=datetime.datetime(2025, 1, 2, tzinfo=datetime.UTC),
            to_date=datetime.datetime(2025, 1, 4, tzinfo=datetime.UTC),
        )

        assert len(items) == 1
        assert total == 3


class TestTransactionRepoGetAll:
    """Tests for SqlaTransactionRepository.get_all()."""

    async def test_get_all_empty(
        self,
        db_session: sa_async.AsyncSession,
    ) -> None:
        """get_all returns empty list and zero total when no transactions exist."""
        repo = txn_repo_mod.SqlaTransactionRepository(db_session)

        items, total = await repo.get_all()

        assert items == []
        assert total == 0

    async def test_get_all_returns_all_transactions(
        self,
        db_session: sa_async.AsyncSession,
        two_accounts: tuple[models.Account, models.Account],
    ) -> None:
        """get_all returns all transactions with entries."""
        cash, revenue = two_accounts
        repo = txn_repo_mod.SqlaTransactionRepository(db_session)
        for i in range(3):
            txn = _make_transaction_with_timestamp(
                cash.id,
                revenue.id,
                datetime.datetime(2025, 1, i + 1, tzinfo=datetime.UTC),
                description=f"Sale {i + 1}",
            )
            await repo.create(txn)

        items, total = await repo.get_all()

        assert len(items) == 3
        assert total == 3

    async def test_get_all_with_limit(
        self,
        db_session: sa_async.AsyncSession,
        two_accounts: tuple[models.Account, models.Account],
    ) -> None:
        """get_all with limit returns limited items but full total."""
        cash, revenue = two_accounts
        repo = txn_repo_mod.SqlaTransactionRepository(db_session)
        for i in range(3):
            txn = _make_transaction_with_timestamp(
                cash.id,
                revenue.id,
                datetime.datetime(2025, 1, i + 1, tzinfo=datetime.UTC),
                description=f"Sale {i + 1}",
            )
            await repo.create(txn)

        items, total = await repo.get_all(limit=2)

        assert len(items) == 2
        assert total == 3

    async def test_get_all_with_date_filter(
        self,
        db_session: sa_async.AsyncSession,
        two_accounts: tuple[models.Account, models.Account],
    ) -> None:
        """get_all with date filters returns only matching transactions."""
        cash, revenue = two_accounts
        repo = txn_repo_mod.SqlaTransactionRepository(db_session)
        for i in range(3):
            txn = _make_transaction_with_timestamp(
                cash.id,
                revenue.id,
                datetime.datetime(2025, 1, i + 1, tzinfo=datetime.UTC),
                description=f"Sale {i + 1}",
            )
            await repo.create(txn)

        items, total = await repo.get_all(
            from_date=datetime.datetime(2025, 1, 2, tzinfo=datetime.UTC),
        )

        assert len(items) == 2
        assert total == 2
