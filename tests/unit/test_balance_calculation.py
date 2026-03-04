"""Unit tests for balance calculation across all four account types."""

import decimal
import uuid

import ledger.domain.enums as enums
import ledger.domain.models as models
import ledger.domain.services as services


def _entry(
    account_id: uuid.UUID,
    entry_type: enums.EntryType,
    amount: str,
) -> models.TransactionEntry:
    """
    Create a TransactionEntry for testing.

    :param account_id: account this entry belongs to
    :param entry_type: DEBIT or CREDIT
    :param amount: decimal amount as string
    :return: constructed TransactionEntry
    """
    return models.TransactionEntry(
        id=uuid.uuid4(),
        transaction_id=uuid.uuid4(),
        account_id=account_id,
        type=entry_type,
        amount=decimal.Decimal(amount),
    )


class TestAssetBalance:
    """ASSET is debit-normal: balance = debits - credits."""

    def test_no_entries_returns_zero(self) -> None:
        """Verify empty entries yield zero balance."""
        assert services.calculate_balance(
            enums.AccountType.ASSET, []
        ) == decimal.Decimal("0")

    def test_debit_increases_balance(self) -> None:
        """Verify debit increases ASSET balance."""
        acc_id = uuid.uuid4()
        entries = [_entry(acc_id, enums.EntryType.DEBIT, "500.00")]
        assert services.calculate_balance(
            enums.AccountType.ASSET, entries
        ) == decimal.Decimal("500.00")

    def test_credit_decreases_balance(self) -> None:
        """Verify credit decreases ASSET balance."""
        acc_id = uuid.uuid4()
        entries = [
            _entry(acc_id, enums.EntryType.DEBIT, "500.00"),
            _entry(acc_id, enums.EntryType.CREDIT, "200.00"),
        ]
        assert services.calculate_balance(
            enums.AccountType.ASSET, entries
        ) == decimal.Decimal("300.00")

    def test_multiple_transactions(self) -> None:
        """Verify cumulative balance across multiple entries."""
        acc_id = uuid.uuid4()
        entries = [
            _entry(acc_id, enums.EntryType.DEBIT, "1000.00"),
            _entry(acc_id, enums.EntryType.CREDIT, "150.00"),
            _entry(acc_id, enums.EntryType.DEBIT, "500.00"),
            _entry(acc_id, enums.EntryType.CREDIT, "75.50"),
        ]
        assert services.calculate_balance(
            enums.AccountType.ASSET, entries
        ) == decimal.Decimal("1274.50")


class TestExpenseBalance:
    """EXPENSE is debit-normal: balance = debits - credits."""

    def test_no_entries_returns_zero(self) -> None:
        """Verify empty entries yield zero balance."""
        assert services.calculate_balance(
            enums.AccountType.EXPENSE, []
        ) == decimal.Decimal("0")

    def test_debit_increases_balance(self) -> None:
        """Verify debit increases EXPENSE balance."""
        acc_id = uuid.uuid4()
        entries = [_entry(acc_id, enums.EntryType.DEBIT, "250.00")]
        assert services.calculate_balance(
            enums.AccountType.EXPENSE, entries
        ) == decimal.Decimal("250.00")

    def test_credit_decreases_balance(self) -> None:
        """Verify credit decreases EXPENSE balance."""
        acc_id = uuid.uuid4()
        entries = [
            _entry(acc_id, enums.EntryType.DEBIT, "300.00"),
            _entry(acc_id, enums.EntryType.CREDIT, "100.00"),
        ]
        assert services.calculate_balance(
            enums.AccountType.EXPENSE, entries
        ) == decimal.Decimal("200.00")


class TestLiabilityBalance:
    """LIABILITY is credit-normal: balance = credits - debits."""

    def test_no_entries_returns_zero(self) -> None:
        """Verify empty entries yield zero balance."""
        assert services.calculate_balance(
            enums.AccountType.LIABILITY, []
        ) == decimal.Decimal("0")

    def test_credit_increases_balance(self) -> None:
        """Verify credit increases LIABILITY balance."""
        acc_id = uuid.uuid4()
        entries = [_entry(acc_id, enums.EntryType.CREDIT, "1000.00")]
        assert services.calculate_balance(
            enums.AccountType.LIABILITY, entries
        ) == decimal.Decimal("1000.00")

    def test_debit_decreases_balance(self) -> None:
        """Verify debit decreases LIABILITY balance."""
        acc_id = uuid.uuid4()
        entries = [
            _entry(acc_id, enums.EntryType.CREDIT, "1000.00"),
            _entry(acc_id, enums.EntryType.DEBIT, "400.00"),
        ]
        assert services.calculate_balance(
            enums.AccountType.LIABILITY, entries
        ) == decimal.Decimal("600.00")


class TestRevenueBalance:
    """REVENUE is credit-normal: balance = credits - debits."""

    def test_no_entries_returns_zero(self) -> None:
        """Verify empty entries yield zero balance."""
        assert services.calculate_balance(
            enums.AccountType.REVENUE, []
        ) == decimal.Decimal("0")

    def test_credit_increases_balance(self) -> None:
        """Verify credit increases REVENUE balance."""
        acc_id = uuid.uuid4()
        entries = [_entry(acc_id, enums.EntryType.CREDIT, "750.00")]
        assert services.calculate_balance(
            enums.AccountType.REVENUE, entries
        ) == decimal.Decimal("750.00")

    def test_debit_decreases_balance(self) -> None:
        """Verify debit decreases REVENUE balance."""
        acc_id = uuid.uuid4()
        entries = [
            _entry(acc_id, enums.EntryType.CREDIT, "750.00"),
            _entry(acc_id, enums.EntryType.DEBIT, "200.00"),
        ]
        assert services.calculate_balance(
            enums.AccountType.REVENUE, entries
        ) == decimal.Decimal("550.00")


class TestEdgeCases:
    """Edge cases for balance calculation."""

    def test_balance_with_small_decimals(self) -> None:
        """Verify precision with small decimal amounts."""
        acc_id = uuid.uuid4()
        entries = [
            _entry(acc_id, enums.EntryType.DEBIT, "0.01"),
            _entry(acc_id, enums.EntryType.DEBIT, "0.02"),
        ]
        assert services.calculate_balance(
            enums.AccountType.ASSET, entries
        ) == decimal.Decimal("0.03")

    def test_balance_with_large_amounts(self) -> None:
        """Verify handling of large monetary amounts."""
        acc_id = uuid.uuid4()
        entries = [_entry(acc_id, enums.EntryType.DEBIT, "999999999.99")]
        assert services.calculate_balance(
            enums.AccountType.ASSET, entries
        ) == decimal.Decimal("999999999.99")

    def test_balance_can_be_negative(self) -> None:
        """An asset account credited more than debited has negative balance."""
        acc_id = uuid.uuid4()
        entries = [
            _entry(acc_id, enums.EntryType.DEBIT, "100.00"),
            _entry(acc_id, enums.EntryType.CREDIT, "300.00"),
        ]
        assert services.calculate_balance(
            enums.AccountType.ASSET, entries
        ) == decimal.Decimal("-200.00")
