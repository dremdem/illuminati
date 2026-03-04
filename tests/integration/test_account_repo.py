"""Integration tests for SqlaAccountRepository against a real PostgreSQL database."""

import uuid

import pytest
import sqlalchemy.ext.asyncio as sa_async

import ledger.domain.enums as enums
import ledger.domain.exceptions as exceptions
import ledger.domain.models as models
import ledger.infrastructure.repositories.account_repo as account_repo_mod


class TestAccountRepoCreate:
    """Tests for SqlaAccountRepository.create()."""

    async def test_create_persists_account(
        self, db_session: sa_async.AsyncSession
    ) -> None:
        """Create persists an account and returns the domain entity."""
        repo = account_repo_mod.SqlaAccountRepository(db_session)
        account = models.Account(
            id=uuid.uuid4(),
            name="Cash",
            type=enums.AccountType.ASSET,
        )

        result = await repo.create(account)

        assert result.id == account.id
        assert result.name == "Cash"
        assert result.type == enums.AccountType.ASSET

    async def test_create_duplicate_name_raises(
        self, db_session: sa_async.AsyncSession
    ) -> None:
        """Create raises DuplicateAccountError for duplicate account names."""
        repo = account_repo_mod.SqlaAccountRepository(db_session)
        account_1 = models.Account(
            id=uuid.uuid4(),
            name="Duplicate",
            type=enums.AccountType.ASSET,
        )
        account_2 = models.Account(
            id=uuid.uuid4(),
            name="Duplicate",
            type=enums.AccountType.LIABILITY,
        )

        await repo.create(account_1)

        with pytest.raises(exceptions.DuplicateAccountError):
            await repo.create(account_2)


class TestAccountRepoGetById:
    """Tests for SqlaAccountRepository.get_by_id()."""

    async def test_get_by_id_found(self, db_session: sa_async.AsyncSession) -> None:
        """get_by_id returns the domain account when it exists."""
        repo = account_repo_mod.SqlaAccountRepository(db_session)
        account = models.Account(
            id=uuid.uuid4(),
            name="Revenue",
            type=enums.AccountType.REVENUE,
        )
        await repo.create(account)

        result = await repo.get_by_id(account.id)

        assert result is not None
        assert result.id == account.id
        assert result.name == "Revenue"
        assert result.type == enums.AccountType.REVENUE

    async def test_get_by_id_not_found(self, db_session: sa_async.AsyncSession) -> None:
        """get_by_id returns None for a non-existent account."""
        repo = account_repo_mod.SqlaAccountRepository(db_session)

        result = await repo.get_by_id(uuid.uuid4())

        assert result is None


class TestAccountRepoGetAll:
    """Tests for SqlaAccountRepository.get_all()."""

    async def test_get_all_empty(self, db_session: sa_async.AsyncSession) -> None:
        """get_all returns an empty list when no accounts exist."""
        repo = account_repo_mod.SqlaAccountRepository(db_session)

        result = await repo.get_all()

        assert result == []

    async def test_get_all_returns_all_accounts(
        self, db_session: sa_async.AsyncSession
    ) -> None:
        """get_all returns all persisted accounts as domain entities."""
        repo = account_repo_mod.SqlaAccountRepository(db_session)
        accounts = [
            models.Account(id=uuid.uuid4(), name="Cash", type=enums.AccountType.ASSET),
            models.Account(
                id=uuid.uuid4(), name="Loan", type=enums.AccountType.LIABILITY
            ),
            models.Account(
                id=uuid.uuid4(), name="Sales", type=enums.AccountType.REVENUE
            ),
        ]
        for acc in accounts:
            await repo.create(acc)

        result = await repo.get_all()

        assert len(result) == 3
        names = {a.name for a in result}
        assert names == {"Cash", "Loan", "Sales"}


class TestAccountRepoExists:
    """Tests for SqlaAccountRepository.exists()."""

    async def test_exists_true(self, db_session: sa_async.AsyncSession) -> None:
        """exists returns True for an existing account."""
        repo = account_repo_mod.SqlaAccountRepository(db_session)
        account = models.Account(
            id=uuid.uuid4(),
            name="Expense",
            type=enums.AccountType.EXPENSE,
        )
        await repo.create(account)

        assert await repo.exists(account.id) is True

    async def test_exists_false(self, db_session: sa_async.AsyncSession) -> None:
        """exists returns False for a non-existent account."""
        repo = account_repo_mod.SqlaAccountRepository(db_session)

        assert await repo.exists(uuid.uuid4()) is False
