"""Integration tests for SQL-based balance computation in AccountRepository."""

import datetime
import decimal
import uuid

import pytest
import sqlalchemy.ext.asyncio as sa_async

import ledger.domain.enums as enums
import ledger.domain.models as models
import ledger.infrastructure.mappers as mappers
import ledger.infrastructure.models as orm_models
import ledger.infrastructure.repositories.account_repo as account_repo_mod


async def _create_account(
    session: sa_async.AsyncSession,
    name: str,
    account_type: enums.AccountType,
) -> models.Account:
    """
    Persist a domain account via ORM and return it.

    :param session: async database session
    :param name: account display name
    :param account_type: financial classification
    :return: persisted domain account
    """
    account = models.Account(id=uuid.uuid4(), name=name, type=account_type)
    session.add(mappers.account_to_orm(account))
    await session.flush()
    return account


async def _create_transaction(
    session: sa_async.AsyncSession,
    entries: list[tuple[uuid.UUID, enums.EntryType, str]],
    description: str = "txn",
) -> None:
    """
    Persist a transaction with entries via ORM.

    :param session: async database session
    :param entries: list of (account_id, entry_type, amount_str) tuples
    :param description: transaction description
    """
    txn_id = uuid.uuid4()
    orm_txn = orm_models.TransactionModel(
        id=txn_id,
        timestamp=datetime.datetime(2025, 1, 1, tzinfo=datetime.UTC),
        description=description,
    )
    session.add(orm_txn)
    await session.flush()

    for account_id, entry_type, amount_str in entries:
        session.add(
            orm_models.TransactionEntryModel(
                id=uuid.uuid4(),
                transaction_id=txn_id,
                account_id=account_id,
                entry_type=entry_type.value,
                amount=decimal.Decimal(amount_str),
            )
        )
    await session.flush()


@pytest.mark.asyncio
async def test_new_account_has_zero_balance(
    db_session: sa_async.AsyncSession,
) -> None:
    """get_with_balance returns Decimal('0') for an account with no entries."""
    repo = account_repo_mod.SqlaAccountRepository(db_session)
    account = await _create_account(db_session, "Empty", enums.AccountType.ASSET)

    result = await repo.get_with_balance(account.id)

    assert result is not None
    returned_account, balance = result
    assert returned_account.id == account.id
    assert balance == decimal.Decimal("0")


class TestAssetBalance:
    """Balance computation for ASSET accounts (debit-normal)."""

    @pytest.mark.asyncio
    async def test_debit_increases(self, db_session: sa_async.AsyncSession) -> None:
        """ASSET + DEBIT entry produces a positive balance."""
        repo = account_repo_mod.SqlaAccountRepository(db_session)
        cash = await _create_account(db_session, "Cash", enums.AccountType.ASSET)
        revenue = await _create_account(
            db_session, "Revenue", enums.AccountType.REVENUE
        )

        await _create_transaction(
            db_session,
            [
                (cash.id, enums.EntryType.DEBIT, "250.00"),
                (revenue.id, enums.EntryType.CREDIT, "250.00"),
            ],
        )

        result = await repo.get_with_balance(cash.id)
        assert result is not None
        _, balance = result
        assert balance == decimal.Decimal("250.00")

    @pytest.mark.asyncio
    async def test_credit_decreases(self, db_session: sa_async.AsyncSession) -> None:
        """ASSET + DEBIT then CREDIT yields the net balance."""
        repo = account_repo_mod.SqlaAccountRepository(db_session)
        cash = await _create_account(db_session, "Cash", enums.AccountType.ASSET)
        revenue = await _create_account(
            db_session, "Revenue", enums.AccountType.REVENUE
        )

        await _create_transaction(
            db_session,
            [
                (cash.id, enums.EntryType.DEBIT, "500.00"),
                (revenue.id, enums.EntryType.CREDIT, "500.00"),
            ],
        )
        await _create_transaction(
            db_session,
            [
                (revenue.id, enums.EntryType.DEBIT, "150.00"),
                (cash.id, enums.EntryType.CREDIT, "150.00"),
            ],
        )

        result = await repo.get_with_balance(cash.id)
        assert result is not None
        _, balance = result
        assert balance == decimal.Decimal("350.00")


class TestLiabilityBalance:
    """Balance computation for LIABILITY accounts (credit-normal)."""

    @pytest.mark.asyncio
    async def test_credit_increases(self, db_session: sa_async.AsyncSession) -> None:
        """LIABILITY + CREDIT entry produces a positive balance."""
        repo = account_repo_mod.SqlaAccountRepository(db_session)
        loan = await _create_account(db_session, "Loan", enums.AccountType.LIABILITY)
        cash = await _create_account(db_session, "Cash", enums.AccountType.ASSET)

        await _create_transaction(
            db_session,
            [
                (cash.id, enums.EntryType.DEBIT, "1000.00"),
                (loan.id, enums.EntryType.CREDIT, "1000.00"),
            ],
        )

        result = await repo.get_with_balance(loan.id)
        assert result is not None
        _, balance = result
        assert balance == decimal.Decimal("1000.00")

    @pytest.mark.asyncio
    async def test_debit_decreases(self, db_session: sa_async.AsyncSession) -> None:
        """LIABILITY + CREDIT then DEBIT yields the net balance."""
        repo = account_repo_mod.SqlaAccountRepository(db_session)
        loan = await _create_account(db_session, "Loan", enums.AccountType.LIABILITY)
        cash = await _create_account(db_session, "Cash", enums.AccountType.ASSET)

        await _create_transaction(
            db_session,
            [
                (cash.id, enums.EntryType.DEBIT, "1000.00"),
                (loan.id, enums.EntryType.CREDIT, "1000.00"),
            ],
        )
        await _create_transaction(
            db_session,
            [
                (loan.id, enums.EntryType.DEBIT, "300.00"),
                (cash.id, enums.EntryType.CREDIT, "300.00"),
            ],
        )

        result = await repo.get_with_balance(loan.id)
        assert result is not None
        _, balance = result
        assert balance == decimal.Decimal("700.00")


class TestExpenseBalance:
    """Balance computation for EXPENSE accounts (debit-normal)."""

    @pytest.mark.asyncio
    async def test_debit_increases(self, db_session: sa_async.AsyncSession) -> None:
        """EXPENSE + DEBIT entry produces a positive balance."""
        repo = account_repo_mod.SqlaAccountRepository(db_session)
        rent = await _create_account(db_session, "Rent", enums.AccountType.EXPENSE)
        cash = await _create_account(db_session, "Cash", enums.AccountType.ASSET)

        await _create_transaction(
            db_session,
            [
                (rent.id, enums.EntryType.DEBIT, "800.00"),
                (cash.id, enums.EntryType.CREDIT, "800.00"),
            ],
        )

        result = await repo.get_with_balance(rent.id)
        assert result is not None
        _, balance = result
        assert balance == decimal.Decimal("800.00")


@pytest.mark.asyncio
async def test_cumulative_multiple_transactions(
    db_session: sa_async.AsyncSession,
) -> None:
    """Multiple transactions on one account accumulate; get_all_with_balances works."""
    repo = account_repo_mod.SqlaAccountRepository(db_session)
    cash = await _create_account(db_session, "Cash", enums.AccountType.ASSET)
    revenue = await _create_account(db_session, "Revenue", enums.AccountType.REVENUE)
    expense = await _create_account(db_session, "Supplies", enums.AccountType.EXPENSE)

    # Txn 1: receive $500 revenue
    await _create_transaction(
        db_session,
        [
            (cash.id, enums.EntryType.DEBIT, "500.00"),
            (revenue.id, enums.EntryType.CREDIT, "500.00"),
        ],
    )
    # Txn 2: receive $300 revenue
    await _create_transaction(
        db_session,
        [
            (cash.id, enums.EntryType.DEBIT, "300.00"),
            (revenue.id, enums.EntryType.CREDIT, "300.00"),
        ],
    )
    # Txn 3: pay $200 for supplies
    await _create_transaction(
        db_session,
        [
            (expense.id, enums.EntryType.DEBIT, "200.00"),
            (cash.id, enums.EntryType.CREDIT, "200.00"),
        ],
    )

    # Verify single account
    result = await repo.get_with_balance(cash.id)
    assert result is not None
    _, cash_balance = result
    assert cash_balance == decimal.Decimal("600.00")

    # Verify get_all_with_balances
    all_results = await repo.get_all_with_balances()
    balances = {account.name: balance for account, balance in all_results}
    assert balances["Cash"] == decimal.Decimal("600.00")
    assert balances["Revenue"] == decimal.Decimal("800.00")
    assert balances["Supplies"] == decimal.Decimal("200.00")
