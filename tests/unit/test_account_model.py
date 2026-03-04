"""Unit tests for Account domain model creation and types."""

import uuid

import ledger.domain.enums as enums
import ledger.domain.models as models


class TestAccountCreation:
    """Tests for creating Account instances with various types."""

    def test_create_asset_account(self) -> None:
        """Verify ASSET account creation."""
        account = models.Account(
            id=uuid.uuid4(), name="Cash", type=enums.AccountType.ASSET
        )
        assert account.name == "Cash"
        assert account.type == enums.AccountType.ASSET

    def test_create_liability_account(self) -> None:
        """Verify LIABILITY account creation."""
        account = models.Account(
            id=uuid.uuid4(),
            name="Bank Loan",
            type=enums.AccountType.LIABILITY,
        )
        assert account.type == enums.AccountType.LIABILITY

    def test_create_revenue_account(self) -> None:
        """Verify REVENUE account creation."""
        account = models.Account(
            id=uuid.uuid4(),
            name="Sales",
            type=enums.AccountType.REVENUE,
        )
        assert account.type == enums.AccountType.REVENUE

    def test_create_expense_account(self) -> None:
        """Verify EXPENSE account creation."""
        account = models.Account(
            id=uuid.uuid4(),
            name="Rent",
            type=enums.AccountType.EXPENSE,
        )
        assert account.type == enums.AccountType.EXPENSE

    def test_account_has_uuid_id(self) -> None:
        """Verify account stores the provided UUID."""
        account_id = uuid.uuid4()
        account = models.Account(
            id=account_id, name="Cash", type=enums.AccountType.ASSET
        )
        assert account.id == account_id

    def test_all_account_types_are_valid(self) -> None:
        """Verify all four account types exist."""
        valid_types = {
            enums.AccountType.ASSET,
            enums.AccountType.LIABILITY,
            enums.AccountType.REVENUE,
            enums.AccountType.EXPENSE,
        }
        assert len(valid_types) == 4
