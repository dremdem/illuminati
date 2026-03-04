"""Application service for account management use cases."""

import dataclasses
import decimal
import uuid

import ledger.application.interfaces as interfaces
import ledger.domain.enums as enums
import ledger.domain.exceptions as exceptions
import ledger.domain.models as models
import ledger.domain.services as domain_services


@dataclasses.dataclass(frozen=True)
class AccountWithBalance:
    """An account paired with its computed balance."""

    account: models.Account
    balance: decimal.Decimal


class AccountService:
    """Orchestrates account creation, retrieval, and balance computation."""

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

    async def create_account(
        self,
        name: str,
        account_type: enums.AccountType,
    ) -> AccountWithBalance:
        """
        Create a new account after validating the name.

        :param name: account display name (must not be empty/whitespace)
        :param account_type: financial account classification
        :return: the created account with zero balance
        :raises DomainError: if name is empty or whitespace-only
        :raises DuplicateAccountError: if name already exists
        """
        if not name or not name.strip():
            raise exceptions.DomainError("Account name must not be empty")

        account = models.Account(
            id=uuid.uuid4(),
            name=name.strip(),
            type=account_type,
        )
        persisted = await self._account_repo.create(account)
        return AccountWithBalance(
            account=persisted,
            balance=decimal.Decimal("0.00"),
        )

    async def get_by_id(self, account_id: uuid.UUID) -> AccountWithBalance:
        """
        Retrieve an account by ID and compute its balance.

        :param account_id: UUID of the account
        :return: account with computed balance
        :raises AccountNotFoundError: if the account does not exist
        """
        account = await self._account_repo.get_by_id(account_id)
        if account is None:
            raise exceptions.AccountNotFoundError(f"Account {account_id} not found")

        balance = await self._compute_balance(account)
        return AccountWithBalance(account=account, balance=balance)

    async def get_all(self) -> list[AccountWithBalance]:
        """
        Retrieve all accounts with computed balances.

        :return: list of accounts with their balances
        """
        accounts = await self._account_repo.get_all()
        results: list[AccountWithBalance] = []
        for account in accounts:
            balance = await self._compute_balance(account)
            results.append(AccountWithBalance(account=account, balance=balance))
        return results

    async def _compute_balance(self, account: models.Account) -> decimal.Decimal:
        """
        Compute the current balance for an account from its transaction entries.

        :param account: the account to compute balance for
        :return: computed balance as Decimal
        """
        transactions = await self._transaction_repo.get_by_account_id(account.id)
        entries: list[models.TransactionEntry] = []
        for txn in transactions:
            for entry in txn.entries:
                if entry.account_id == account.id:
                    entries.append(entry)
        return domain_services.calculate_balance(account.type, entries)
