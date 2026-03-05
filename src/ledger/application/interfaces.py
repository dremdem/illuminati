"""Repository interfaces defining data-access contracts for the application layer."""

import datetime
import decimal
import typing
import uuid

import ledger.domain.models as models


class AccountRepository(typing.Protocol):
    """Data-access contract for account persistence."""

    async def create(self, account: models.Account) -> models.Account:
        """
        Persist a new account.

        :param account: domain account to persist
        :return: the persisted account
        :raises DuplicateAccountError: if an account with the same name exists
        """
        ...

    async def get_by_id(self, account_id: uuid.UUID) -> models.Account | None:
        """
        Retrieve an account by its unique identifier.

        :param account_id: UUID of the account
        :return: the account, or None if not found
        """
        ...

    async def get_all(self) -> list[models.Account]:
        """
        Retrieve all accounts.

        :return: list of all accounts
        """
        ...

    async def exists(self, account_id: uuid.UUID) -> bool:
        """
        Check whether an account exists.

        :param account_id: UUID of the account
        :return: True if the account exists, False otherwise
        """
        ...

    async def get_with_balance(
        self, account_id: uuid.UUID
    ) -> tuple[models.Account, decimal.Decimal] | None:
        """
        Retrieve an account with its computed balance via SQL aggregation.

        :param account_id: UUID of the account
        :return: tuple of (account, balance), or None if not found
        """
        ...

    async def get_all_with_balances(
        self,
        limit: int | None = None,
        offset: int = 0,
    ) -> tuple[list[tuple[models.Account, decimal.Decimal]], int]:
        """
        Retrieve all accounts with their computed balances via SQL aggregation.

        :param limit: maximum number of accounts to return (None = all)
        :param offset: number of accounts to skip
        :return: tuple of (list of (account, balance) tuples, total count)
        """
        ...


class TransactionRepository(typing.Protocol):
    """Data-access contract for transaction persistence."""

    async def create(self, transaction: models.Transaction) -> models.Transaction:
        """
        Persist a new transaction with its entries.

        :param transaction: domain transaction to persist
        :return: the persisted transaction
        """
        ...

    async def get_by_id(self, transaction_id: uuid.UUID) -> models.Transaction | None:
        """
        Retrieve a transaction by its unique identifier.

        :param transaction_id: UUID of the transaction
        :return: the transaction with entries, or None if not found
        """
        ...

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

        Returns full transactions with ALL entries (not just the matching
        account's), preserving the double-entry invariant.

        :param account_id: UUID of the account
        :param limit: maximum number of transactions to return (None = all)
        :param offset: number of transactions to skip
        :param from_date: inclusive lower bound on transaction timestamp
        :param to_date: inclusive upper bound on transaction timestamp
        :return: tuple of (list of transactions, total count)
        """
        ...

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
        ...
