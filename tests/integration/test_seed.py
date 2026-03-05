"""Integration tests for the data-seeding script."""

import collections.abc
import decimal

import pytest
import sqlalchemy as sa
import sqlalchemy.ext.asyncio as sa_async

import ledger.infrastructure.repositories.account_repo as account_repo_mod
import ledger.scripts.seed as seed_mod

EXPECTED_BALANCES: dict[str, decimal.Decimal] = {
    "Cash": decimal.Decimal("700.00"),
    "Office Supplies": decimal.Decimal("600.00"),
    "Accounts Payable": decimal.Decimal("0.00"),
    "Sales Revenue": decimal.Decimal("1000.00"),
    "Accounts Receivable": decimal.Decimal("0.00"),
    "Inventory": decimal.Decimal("0.00"),
    "Cost of Goods Sold": decimal.Decimal("600.00"),
    "Bank Loan": decimal.Decimal("1000.00"),
    "Loan Fees": decimal.Decimal("50.00"),
    "Interest Expense": decimal.Decimal("50.00"),
}


@pytest.fixture(autouse=True)
async def _cleanup_seed_data(
    async_engine: sa_async.AsyncEngine,
) -> collections.abc.AsyncGenerator[None, None]:
    """
    Remove all committed seed data after each test.

    The seed function commits directly to the database, so unlike
    ``db_session``-based tests the data persists across tests.

    :param async_engine: session-scoped async engine
    """
    yield
    async with async_engine.begin() as conn:
        await conn.execute(sa.text("DELETE FROM transaction_entries"))
        await conn.execute(sa.text("DELETE FROM transactions"))
        await conn.execute(sa.text("DELETE FROM accounts"))


@pytest.mark.asyncio
async def test_seed_creates_accounts_with_correct_balances(
    async_engine: sa_async.AsyncEngine,
) -> None:
    """Seed creates 10 accounts and 7 transactions with expected balances."""
    session_factory = sa_async.async_sessionmaker(async_engine, expire_on_commit=False)

    await seed_mod.seed(session_factory)

    async with session_factory() as session:
        repo = account_repo_mod.SqlaAccountRepository(session)
        items, total = await repo.get_all_with_balances()
        balances = {account.name: balance for account, balance in items}

    assert total == len(EXPECTED_BALANCES)
    assert len(balances) == len(EXPECTED_BALANCES)
    for name, expected in EXPECTED_BALANCES.items():
        assert balances[name] == expected, f"{name}: {balances[name]} != {expected}"


@pytest.mark.asyncio
async def test_seed_is_idempotent(
    async_engine: sa_async.AsyncEngine,
) -> None:
    """Running seed twice does not duplicate accounts or crash."""
    session_factory = sa_async.async_sessionmaker(async_engine, expire_on_commit=False)

    await seed_mod.seed(session_factory)
    await seed_mod.seed(session_factory)

    async with session_factory() as session:
        repo = account_repo_mod.SqlaAccountRepository(session)
        items, total = await repo.get_all_with_balances()
        balances = {account.name: balance for account, balance in items}

    assert total == len(EXPECTED_BALANCES)
    assert len(balances) == len(EXPECTED_BALANCES)
    for name, expected in EXPECTED_BALANCES.items():
        assert balances[name] == expected, f"{name}: {balances[name]} != {expected}"
