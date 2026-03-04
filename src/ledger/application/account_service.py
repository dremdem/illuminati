"""Application service for account management use cases."""

import dataclasses
import decimal
import uuid

import ledger.application.interfaces as interfaces
import ledger.domain.enums as enums
import ledger.domain.exceptions as exceptions
import ledger.domain.models as models


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
    ) -> None:
        """
        Initialise the service with repository dependencies.

        :param account_repo: account persistence interface
        """
        self._account_repo = account_repo

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
        Retrieve an account by ID with its balance computed via SQL aggregation.

        :param account_id: UUID of the account
        :return: account with computed balance
        :raises AccountNotFoundError: if the account does not exist
        """
        result = await self._account_repo.get_with_balance(account_id)
        if result is None:
            raise exceptions.AccountNotFoundError(f"Account {account_id} not found")

        account, balance = result
        return AccountWithBalance(account=account, balance=balance)

    async def get_all(self) -> list[AccountWithBalance]:
        """
        Retrieve all accounts with balances computed via SQL aggregation.

        :return: list of accounts with their balances
        """
        results = await self._account_repo.get_all_with_balances()
        return [
            AccountWithBalance(account=account, balance=balance)
            for account, balance in results
        ]
