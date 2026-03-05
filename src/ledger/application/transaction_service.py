"""Application service for transaction processing use cases."""

import dataclasses
import datetime
import decimal
import uuid

import ledger.application.interfaces as interfaces
import ledger.domain.enums as enums
import ledger.domain.exceptions as exceptions
import ledger.domain.models as models
import ledger.domain.services as domain_services


@dataclasses.dataclass(frozen=True)
class EntryData:
    """Input data for a single transaction entry (from API layer)."""

    account_id: uuid.UUID
    type: enums.EntryType
    amount: decimal.Decimal


class TransactionService:
    """Orchestrates transaction creation, retrieval, and validation."""

    def __init__(
        self,
        account_repo: interfaces.AccountRepository,
        transaction_repo: interfaces.TransactionRepository,
    ) -> None:
        """
        Initialise the service with repository dependencies.

        :param account_repo: account persistence interface
        :param transaction_repo: transaction persistence interface
        """
        self._account_repo = account_repo
        self._transaction_repo = transaction_repo

    async def create_transaction(
        self,
        description: str,
        timestamp: datetime.datetime,
        entries_data: list[EntryData],
    ) -> models.Transaction:
        """
        Create a new transaction after validating accounts and entries.

        Checks that all referenced accounts exist before running domain
        validation, so that missing-account errors produce 404 (not 400).

        :param description: human-readable transaction description
        :param timestamp: when the transaction occurred
        :param entries_data: list of entry inputs (account, type, amount)
        :return: the persisted transaction with entries
        :raises AccountNotFoundError: if any referenced account does not exist
        :raises InvalidTransactionError: if entries violate structural rules
        :raises UnbalancedTransactionError: if debits != credits
        """
        for entry_data in entries_data:
            exists = await self._account_repo.exists(entry_data.account_id)
            if not exists:
                raise exceptions.AccountNotFoundError(
                    f"Account {entry_data.account_id} not found"
                )

        txn_id = uuid.uuid4()
        entries = [
            models.TransactionEntry(
                id=uuid.uuid4(),
                transaction_id=txn_id,
                account_id=ed.account_id,
                type=ed.type,
                amount=ed.amount,
            )
            for ed in entries_data
        ]

        domain_services.validate_transaction_entries(entries, description)

        transaction = models.Transaction(
            id=txn_id,
            timestamp=timestamp,
            description=description,
            entries=entries,
        )

        return await self._transaction_repo.create(transaction)

    async def get_by_id(self, transaction_id: uuid.UUID) -> models.Transaction:
        """
        Retrieve a transaction by ID.

        :param transaction_id: UUID of the transaction
        :return: the transaction with all entries
        :raises TransactionNotFoundError: if the transaction does not exist
        """
        txn = await self._transaction_repo.get_by_id(transaction_id)
        if txn is None:
            raise exceptions.TransactionNotFoundError(
                f"Transaction {transaction_id} not found"
            )
        return txn

    async def get_by_account_id(
        self,
        account_id: uuid.UUID,
        limit: int | None = None,
        offset: int = 0,
        from_date: datetime.datetime | None = None,
        to_date: datetime.datetime | None = None,
    ) -> list[models.Transaction]:
        """
        Retrieve transactions involving a given account with optional filtering.

        :param account_id: UUID of the account
        :param limit: maximum number of transactions to return (None = all)
        :param offset: number of transactions to skip
        :param from_date: inclusive lower bound on transaction timestamp
        :param to_date: inclusive upper bound on transaction timestamp
        :return: list of transactions with entries
        :raises AccountNotFoundError: if the account does not exist
        """
        account = await self._account_repo.get_by_id(account_id)
        if account is None:
            raise exceptions.AccountNotFoundError(f"Account {account_id} not found")
        return await self._transaction_repo.get_by_account_id(
            account_id,
            limit=limit,
            offset=offset,
            from_date=from_date,
            to_date=to_date,
        )
