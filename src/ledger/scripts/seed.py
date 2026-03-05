"""Seed the database with sample accounts and transactions.

Demonstrates three real-world business scenarios:
1. Purchase office supplies (cash + credit)
2. Sell goods on credit (inventory purchase, sale, payment)
3. Borrow money from a bank (loan disbursement, interest payment)

Usage::

    python -m ledger.scripts.seed
"""

import asyncio
import datetime
import decimal
import os
import uuid

import sqlalchemy.ext.asyncio as sa_async

import ledger.application.account_service as account_service_mod
import ledger.application.transaction_service as transaction_service_mod
import ledger.domain.enums as enums
import ledger.domain.exceptions as exceptions
import ledger.infrastructure.database as database
import ledger.infrastructure.repositories.account_repo as account_repo_mod
import ledger.infrastructure.repositories.transaction_repo as transaction_repo_mod

_ACCOUNTS: list[tuple[str, enums.AccountType]] = [
    ("Cash", enums.AccountType.ASSET),
    ("Office Supplies", enums.AccountType.EXPENSE),
    ("Accounts Payable", enums.AccountType.LIABILITY),
    ("Sales Revenue", enums.AccountType.REVENUE),
    ("Accounts Receivable", enums.AccountType.ASSET),
    ("Inventory", enums.AccountType.ASSET),
    ("Cost of Goods Sold", enums.AccountType.EXPENSE),
    ("Bank Loan", enums.AccountType.LIABILITY),
    ("Loan Fees", enums.AccountType.EXPENSE),
    ("Interest Expense", enums.AccountType.EXPENSE),
]


def _entry(
    account_id: uuid.UUID,
    entry_type: enums.EntryType,
    amount: str,
) -> transaction_service_mod.EntryData:
    """
    Build an EntryData shorthand.

    :param account_id: UUID of the account
    :param entry_type: DEBIT or CREDIT
    :param amount: decimal amount as string
    :return: EntryData instance
    """
    return transaction_service_mod.EntryData(
        account_id=account_id,
        type=entry_type,
        amount=decimal.Decimal(amount),
    )


async def seed(
    session_factory: sa_async.async_sessionmaker[sa_async.AsyncSession],
) -> None:
    """
    Populate the database with 10 accounts and 7 transactions.

    Idempotent: skips account creation when names already exist and only
    creates transactions when accounts were freshly created.

    :param session_factory: async session factory bound to the target engine
    """
    dr = enums.EntryType.DEBIT
    cr = enums.EntryType.CREDIT

    ids: dict[str, uuid.UUID] = {}
    created_new = False

    # --- accounts ---
    async with session_factory() as session:
        acct_repo = account_repo_mod.SqlaAccountRepository(session)
        acct_svc = account_service_mod.AccountService(account_repo=acct_repo)

        for name, acct_type in _ACCOUNTS:
            try:
                result = await acct_svc.create_account(name, acct_type)
                ids[name] = result.account.id
                created_new = True
            except exceptions.DuplicateAccountError:
                pass

        await session.commit()

    if not created_new:
        print("Seed data already exists -- skipping transactions.")
        return

    # If some accounts were created but others already existed, fetch all IDs
    async with session_factory() as session:
        acct_repo = account_repo_mod.SqlaAccountRepository(session)
        all_accounts = await acct_repo.get_all()
        for acct in all_accounts:
            ids[acct.name] = acct.id

    # --- transactions ---
    transactions = [
        # 1. Purchase office supplies: $200 cash + $400 on credit
        (
            "Purchase office supplies",
            datetime.datetime(2026, 3, 1, 10, 0, tzinfo=datetime.UTC),
            [
                _entry(ids["Office Supplies"], dr, "600.00"),
                _entry(ids["Cash"], cr, "200.00"),
                _entry(ids["Accounts Payable"], cr, "400.00"),
            ],
        ),
        # 2. Purchase inventory for resale
        (
            "Purchase inventory for resale",
            datetime.datetime(2026, 3, 3, 10, 0, tzinfo=datetime.UTC),
            [
                _entry(ids["Inventory"], dr, "600.00"),
                _entry(ids["Cash"], cr, "600.00"),
            ],
        ),
        # 3. Pay office supply supplier
        (
            "Pay office supply supplier",
            datetime.datetime(2026, 3, 5, 10, 0, tzinfo=datetime.UTC),
            [
                _entry(ids["Accounts Payable"], dr, "400.00"),
                _entry(ids["Cash"], cr, "400.00"),
            ],
        ),
        # 4. Sale of goods on credit
        (
            "Sale of goods on credit",
            datetime.datetime(2026, 3, 10, 14, 0, tzinfo=datetime.UTC),
            [
                _entry(ids["Accounts Receivable"], dr, "1000.00"),
                _entry(ids["Sales Revenue"], cr, "1000.00"),
                _entry(ids["Cost of Goods Sold"], dr, "600.00"),
                _entry(ids["Inventory"], cr, "600.00"),
            ],
        ),
        # 5. Customer payment for goods
        (
            "Customer payment for goods",
            datetime.datetime(2026, 3, 15, 9, 0, tzinfo=datetime.UTC),
            [
                _entry(ids["Cash"], dr, "1000.00"),
                _entry(ids["Accounts Receivable"], cr, "1000.00"),
            ],
        ),
        # 6. Bank loan received (with $50 origination fee)
        (
            "Bank loan received",
            datetime.datetime(2026, 3, 20, 11, 0, tzinfo=datetime.UTC),
            [
                _entry(ids["Cash"], dr, "950.00"),
                _entry(ids["Loan Fees"], dr, "50.00"),
                _entry(ids["Bank Loan"], cr, "1000.00"),
            ],
        ),
        # 7. Loan interest payment
        (
            "Loan interest payment",
            datetime.datetime(2026, 4, 1, 10, 0, tzinfo=datetime.UTC),
            [
                _entry(ids["Interest Expense"], dr, "50.00"),
                _entry(ids["Cash"], cr, "50.00"),
            ],
        ),
    ]

    async with session_factory() as session:
        acct_repo = account_repo_mod.SqlaAccountRepository(session)
        txn_repo = transaction_repo_mod.SqlaTransactionRepository(session)
        txn_svc = transaction_service_mod.TransactionService(
            account_repo=acct_repo,
            transaction_repo=txn_repo,
        )

        for description, timestamp, entries in transactions:
            await txn_svc.create_transaction(
                description=description,
                timestamp=timestamp,
                entries_data=entries,
            )

        await session.commit()

    # --- summary ---
    async with session_factory() as session:
        acct_repo = account_repo_mod.SqlaAccountRepository(session)
        results, total = await acct_repo.get_all_with_balances()

    print("Seed data loaded successfully!")
    print()
    print(f"{'Account':<25} {'Type':<12} {'Balance':>12}")
    print("-" * 50)
    for account, balance in results:
        print(f"{account.name:<25} {account.type.value:<12} {balance:>12,.2f}")


async def _main() -> None:
    """
    Entry point: read DATABASE_URL, create engine, and run seed.

    :raises RuntimeError: if DATABASE_URL is not set
    """
    database_url = os.environ.get("DATABASE_URL")
    if database_url is None:
        raise RuntimeError("DATABASE_URL environment variable is required")

    engine = database.create_async_engine(database_url)
    session_factory = database.create_async_session_factory(engine)

    try:
        await seed(session_factory)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(_main())
