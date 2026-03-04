"""Unit tests for Account domain model creation and types."""

from uuid import uuid4

from ledger.domain.enums import AccountType
from ledger.domain.models import Account


class TestAccountCreation:
    def test_create_asset_account(self) -> None:
        account = Account(id=uuid4(), name="Cash", type=AccountType.ASSET)
        assert account.name == "Cash"
        assert account.type == AccountType.ASSET

    def test_create_liability_account(self) -> None:
        account = Account(id=uuid4(), name="Bank Loan", type=AccountType.LIABILITY)
        assert account.type == AccountType.LIABILITY

    def test_create_revenue_account(self) -> None:
        account = Account(id=uuid4(), name="Sales", type=AccountType.REVENUE)
        assert account.type == AccountType.REVENUE

    def test_create_expense_account(self) -> None:
        account = Account(id=uuid4(), name="Rent", type=AccountType.EXPENSE)
        assert account.type == AccountType.EXPENSE

    def test_account_has_uuid_id(self) -> None:
        account_id = uuid4()
        account = Account(id=account_id, name="Cash", type=AccountType.ASSET)
        assert account.id == account_id

    def test_all_account_types_are_valid(self) -> None:
        valid_types = {
            AccountType.ASSET,
            AccountType.LIABILITY,
            AccountType.REVENUE,
            AccountType.EXPENSE,
        }
        assert len(valid_types) == 4
