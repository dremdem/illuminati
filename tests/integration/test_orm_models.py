"""Integration tests for SQLAlchemy ORM models against a real PostgreSQL database."""

import datetime
import decimal
import uuid

import pytest
import sqlalchemy.exc as sa_exc
import sqlalchemy.ext.asyncio as sa_async

import ledger.infrastructure.models as models


class TestAccountModel:
    """Tests for AccountModel CRUD and constraints."""

    async def test_create_account(self, db_session: sa_async.AsyncSession) -> None:
        """Insert an account and verify all fields are persisted correctly."""
        account = models.AccountModel(
            id=uuid.uuid4(),
            name="Cash",
            account_type="ASSET",
        )
        db_session.add(account)
        await db_session.flush()

        result = await db_session.get(models.AccountModel, account.id)

        assert result is not None
        assert result.name == "Cash"
        assert result.account_type == "ASSET"
        assert result.created_at is not None

    async def test_created_at_default(self, db_session: sa_async.AsyncSession) -> None:
        """Verify created_at is set by the database server default."""
        account = models.AccountModel(
            id=uuid.uuid4(),
            name="Revenue",
            account_type="REVENUE",
        )
        db_session.add(account)
        await db_session.flush()

        assert isinstance(account.created_at, datetime.datetime)

    async def test_unique_name_constraint(
        self,
        db_session: sa_async.AsyncSession,
    ) -> None:
        """Inserting two accounts with the same name must raise IntegrityError."""
        account_1 = models.AccountModel(
            id=uuid.uuid4(),
            name="Duplicate",
            account_type="ASSET",
        )
        account_2 = models.AccountModel(
            id=uuid.uuid4(),
            name="Duplicate",
            account_type="LIABILITY",
        )
        db_session.add(account_1)
        await db_session.flush()

        db_session.add(account_2)
        with pytest.raises(sa_exc.IntegrityError):
            await db_session.flush()

    async def test_name_not_null(self, db_session: sa_async.AsyncSession) -> None:
        """Account name must not be null."""
        account = models.AccountModel(
            id=uuid.uuid4(),
            name=None,  # type: ignore[arg-type]
            account_type="ASSET",
        )
        db_session.add(account)
        with pytest.raises(sa_exc.IntegrityError):
            await db_session.flush()

    async def test_account_type_not_null(
        self,
        db_session: sa_async.AsyncSession,
    ) -> None:
        """Account type must not be null."""
        account = models.AccountModel(
            id=uuid.uuid4(),
            name="NoType",
            account_type=None,  # type: ignore[arg-type]
        )
        db_session.add(account)
        with pytest.raises(sa_exc.IntegrityError):
            await db_session.flush()

    async def test_invalid_account_type_check(
        self,
        db_session: sa_async.AsyncSession,
    ) -> None:
        """Account type must be one of the allowed enum values."""
        account = models.AccountModel(
            id=uuid.uuid4(),
            name="BadType",
            account_type="INVALID",
        )
        db_session.add(account)
        with pytest.raises(sa_exc.IntegrityError):
            await db_session.flush()


class TestTransactionModel:
    """Tests for TransactionModel CRUD and constraints."""

    async def test_create_transaction(self, db_session: sa_async.AsyncSession) -> None:
        """Insert a transaction and verify all fields are persisted."""
        txn = models.TransactionModel(
            id=uuid.uuid4(),
            timestamp=datetime.datetime.now(tz=datetime.UTC),
            description="Test payment",
        )
        db_session.add(txn)
        await db_session.flush()

        result = await db_session.get(models.TransactionModel, txn.id)

        assert result is not None
        assert result.description == "Test payment"
        assert result.created_at is not None

    async def test_description_not_null(
        self,
        db_session: sa_async.AsyncSession,
    ) -> None:
        """Transaction description must not be null."""
        txn = models.TransactionModel(
            id=uuid.uuid4(),
            timestamp=datetime.datetime.now(tz=datetime.UTC),
            description=None,  # type: ignore[arg-type]
        )
        db_session.add(txn)
        with pytest.raises(sa_exc.IntegrityError):
            await db_session.flush()


class TestTransactionEntryModel:
    """Tests for TransactionEntryModel CRUD, constraints, and relationships."""

    async def test_create_entry_with_relationships(
        self,
        db_session: sa_async.AsyncSession,
    ) -> None:
        """Insert an entry linked to a transaction and account, verify relationship."""
        account = models.AccountModel(
            id=uuid.uuid4(),
            name="Cash",
            account_type="ASSET",
        )
        txn = models.TransactionModel(
            id=uuid.uuid4(),
            timestamp=datetime.datetime.now(tz=datetime.UTC),
            description="Sale",
        )
        db_session.add_all([account, txn])
        await db_session.flush()

        entry = models.TransactionEntryModel(
            id=uuid.uuid4(),
            transaction_id=txn.id,
            account_id=account.id,
            entry_type="DEBIT",
            amount=decimal.Decimal("100.00"),
        )
        db_session.add(entry)
        await db_session.flush()

        result = await db_session.get(models.TransactionEntryModel, entry.id)

        assert result is not None
        assert result.amount == decimal.Decimal("100.00")
        assert result.entry_type == "DEBIT"
        assert result.transaction_id == txn.id
        assert result.account_id == account.id

    async def test_invalid_entry_type_check(
        self,
        db_session: sa_async.AsyncSession,
    ) -> None:
        """Entry type must be DEBIT or CREDIT."""
        account = models.AccountModel(
            id=uuid.uuid4(),
            name="Cash",
            account_type="ASSET",
        )
        txn = models.TransactionModel(
            id=uuid.uuid4(),
            timestamp=datetime.datetime.now(tz=datetime.UTC),
            description="Bad entry",
        )
        db_session.add_all([account, txn])
        await db_session.flush()

        entry = models.TransactionEntryModel(
            id=uuid.uuid4(),
            transaction_id=txn.id,
            account_id=account.id,
            entry_type="WRONG",
            amount=decimal.Decimal("50.00"),
        )
        db_session.add(entry)
        with pytest.raises(sa_exc.IntegrityError):
            await db_session.flush()

    async def test_amount_must_be_positive(
        self,
        db_session: sa_async.AsyncSession,
    ) -> None:
        """Entry amount must be greater than zero."""
        account = models.AccountModel(
            id=uuid.uuid4(),
            name="Cash",
            account_type="ASSET",
        )
        txn = models.TransactionModel(
            id=uuid.uuid4(),
            timestamp=datetime.datetime.now(tz=datetime.UTC),
            description="Negative test",
        )
        db_session.add_all([account, txn])
        await db_session.flush()

        entry = models.TransactionEntryModel(
            id=uuid.uuid4(),
            transaction_id=txn.id,
            account_id=account.id,
            entry_type="DEBIT",
            amount=decimal.Decimal("-10.00"),
        )
        db_session.add(entry)
        with pytest.raises(sa_exc.IntegrityError):
            await db_session.flush()

    async def test_zero_amount_rejected(
        self,
        db_session: sa_async.AsyncSession,
    ) -> None:
        """Entry amount of zero must be rejected by the check constraint."""
        account = models.AccountModel(
            id=uuid.uuid4(),
            name="Cash",
            account_type="ASSET",
        )
        txn = models.TransactionModel(
            id=uuid.uuid4(),
            timestamp=datetime.datetime.now(tz=datetime.UTC),
            description="Zero test",
        )
        db_session.add_all([account, txn])
        await db_session.flush()

        entry = models.TransactionEntryModel(
            id=uuid.uuid4(),
            transaction_id=txn.id,
            account_id=account.id,
            entry_type="DEBIT",
            amount=decimal.Decimal("0"),
        )
        db_session.add(entry)
        with pytest.raises(sa_exc.IntegrityError):
            await db_session.flush()

    async def test_foreign_key_transaction(
        self,
        db_session: sa_async.AsyncSession,
    ) -> None:
        """Entry must reference an existing transaction."""
        account = models.AccountModel(
            id=uuid.uuid4(),
            name="Cash",
            account_type="ASSET",
        )
        db_session.add(account)
        await db_session.flush()

        entry = models.TransactionEntryModel(
            id=uuid.uuid4(),
            transaction_id=uuid.uuid4(),
            account_id=account.id,
            entry_type="DEBIT",
            amount=decimal.Decimal("50.00"),
        )
        db_session.add(entry)
        with pytest.raises(sa_exc.IntegrityError):
            await db_session.flush()

    async def test_foreign_key_account(
        self,
        db_session: sa_async.AsyncSession,
    ) -> None:
        """Entry must reference an existing account."""
        txn = models.TransactionModel(
            id=uuid.uuid4(),
            timestamp=datetime.datetime.now(tz=datetime.UTC),
            description="No account",
        )
        db_session.add(txn)
        await db_session.flush()

        entry = models.TransactionEntryModel(
            id=uuid.uuid4(),
            transaction_id=txn.id,
            account_id=uuid.uuid4(),
            entry_type="CREDIT",
            amount=decimal.Decimal("25.00"),
        )
        db_session.add(entry)
        with pytest.raises(sa_exc.IntegrityError):
            await db_session.flush()

    async def test_cascade_delete_entries(
        self,
        db_session: sa_async.AsyncSession,
    ) -> None:
        """Deleting a transaction must cascade-delete its entries."""
        account = models.AccountModel(
            id=uuid.uuid4(),
            name="Cash",
            account_type="ASSET",
        )
        txn = models.TransactionModel(
            id=uuid.uuid4(),
            timestamp=datetime.datetime.now(tz=datetime.UTC),
            description="Cascade test",
        )
        db_session.add_all([account, txn])
        await db_session.flush()

        entry = models.TransactionEntryModel(
            id=uuid.uuid4(),
            transaction_id=txn.id,
            account_id=account.id,
            entry_type="DEBIT",
            amount=decimal.Decimal("75.00"),
        )
        db_session.add(entry)
        await db_session.flush()
        entry_id = entry.id

        await db_session.delete(txn)
        await db_session.flush()

        orphan = await db_session.get(models.TransactionEntryModel, entry_id)
        assert orphan is None

    async def test_entries_relationship_on_transaction(
        self,
        db_session: sa_async.AsyncSession,
    ) -> None:
        """Transaction.entries relationship loads related entries."""
        account = models.AccountModel(
            id=uuid.uuid4(),
            name="Cash",
            account_type="ASSET",
        )
        txn = models.TransactionModel(
            id=uuid.uuid4(),
            timestamp=datetime.datetime.now(tz=datetime.UTC),
            description="Relationship test",
        )
        entry = models.TransactionEntryModel(
            id=uuid.uuid4(),
            account_id=account.id,
            entry_type="DEBIT",
            amount=decimal.Decimal("200.00"),
        )
        txn.entries.append(entry)
        db_session.add_all([account, txn])
        await db_session.flush()

        loaded = await db_session.get(models.TransactionModel, txn.id)
        assert loaded is not None
        assert len(loaded.entries) == 1
        assert loaded.entries[0].amount == decimal.Decimal("200.00")
