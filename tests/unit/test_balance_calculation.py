from decimal import Decimal
from uuid import uuid4

from ledger.domain.enums import AccountType, EntryType
from ledger.domain.models import TransactionEntry
from ledger.domain.services import calculate_balance


def _entry(
    account_id: "uuid4",  # type: ignore[type-arg]
    entry_type: EntryType,
    amount: str,
) -> TransactionEntry:
    return TransactionEntry(
        id=uuid4(),
        transaction_id=uuid4(),
        account_id=account_id,
        type=entry_type,
        amount=Decimal(amount),
    )


class TestAssetBalance:
    """ASSET is debit-normal: balance = debits - credits."""

    def test_no_entries_returns_zero(self) -> None:
        assert calculate_balance(AccountType.ASSET, []) == Decimal("0")

    def test_debit_increases_balance(self) -> None:
        acc_id = uuid4()
        entries = [_entry(acc_id, EntryType.DEBIT, "500.00")]
        assert calculate_balance(AccountType.ASSET, entries) == Decimal("500.00")

    def test_credit_decreases_balance(self) -> None:
        acc_id = uuid4()
        entries = [
            _entry(acc_id, EntryType.DEBIT, "500.00"),
            _entry(acc_id, EntryType.CREDIT, "200.00"),
        ]
        assert calculate_balance(AccountType.ASSET, entries) == Decimal("300.00")

    def test_multiple_transactions(self) -> None:
        acc_id = uuid4()
        entries = [
            _entry(acc_id, EntryType.DEBIT, "1000.00"),
            _entry(acc_id, EntryType.CREDIT, "150.00"),
            _entry(acc_id, EntryType.DEBIT, "500.00"),
            _entry(acc_id, EntryType.CREDIT, "75.50"),
        ]
        assert calculate_balance(AccountType.ASSET, entries) == Decimal("1274.50")


class TestExpenseBalance:
    """EXPENSE is debit-normal: balance = debits - credits."""

    def test_no_entries_returns_zero(self) -> None:
        assert calculate_balance(AccountType.EXPENSE, []) == Decimal("0")

    def test_debit_increases_balance(self) -> None:
        acc_id = uuid4()
        entries = [_entry(acc_id, EntryType.DEBIT, "250.00")]
        assert calculate_balance(AccountType.EXPENSE, entries) == Decimal("250.00")

    def test_credit_decreases_balance(self) -> None:
        acc_id = uuid4()
        entries = [
            _entry(acc_id, EntryType.DEBIT, "300.00"),
            _entry(acc_id, EntryType.CREDIT, "100.00"),
        ]
        assert calculate_balance(AccountType.EXPENSE, entries) == Decimal("200.00")


class TestLiabilityBalance:
    """LIABILITY is credit-normal: balance = credits - debits."""

    def test_no_entries_returns_zero(self) -> None:
        assert calculate_balance(AccountType.LIABILITY, []) == Decimal("0")

    def test_credit_increases_balance(self) -> None:
        acc_id = uuid4()
        entries = [_entry(acc_id, EntryType.CREDIT, "1000.00")]
        assert calculate_balance(AccountType.LIABILITY, entries) == Decimal("1000.00")

    def test_debit_decreases_balance(self) -> None:
        acc_id = uuid4()
        entries = [
            _entry(acc_id, EntryType.CREDIT, "1000.00"),
            _entry(acc_id, EntryType.DEBIT, "400.00"),
        ]
        assert calculate_balance(AccountType.LIABILITY, entries) == Decimal("600.00")


class TestRevenueBalance:
    """REVENUE is credit-normal: balance = credits - debits."""

    def test_no_entries_returns_zero(self) -> None:
        assert calculate_balance(AccountType.REVENUE, []) == Decimal("0")

    def test_credit_increases_balance(self) -> None:
        acc_id = uuid4()
        entries = [_entry(acc_id, EntryType.CREDIT, "750.00")]
        assert calculate_balance(AccountType.REVENUE, entries) == Decimal("750.00")

    def test_debit_decreases_balance(self) -> None:
        acc_id = uuid4()
        entries = [
            _entry(acc_id, EntryType.CREDIT, "750.00"),
            _entry(acc_id, EntryType.DEBIT, "200.00"),
        ]
        assert calculate_balance(AccountType.REVENUE, entries) == Decimal("550.00")


class TestEdgeCases:
    def test_balance_with_small_decimals(self) -> None:
        acc_id = uuid4()
        entries = [
            _entry(acc_id, EntryType.DEBIT, "0.01"),
            _entry(acc_id, EntryType.DEBIT, "0.02"),
        ]
        assert calculate_balance(AccountType.ASSET, entries) == Decimal("0.03")

    def test_balance_with_large_amounts(self) -> None:
        acc_id = uuid4()
        entries = [_entry(acc_id, EntryType.DEBIT, "999999999.99")]
        assert calculate_balance(AccountType.ASSET, entries) == Decimal("999999999.99")

    def test_balance_can_be_negative(self) -> None:
        """An asset account credited more than debited has negative balance."""
        acc_id = uuid4()
        entries = [
            _entry(acc_id, EntryType.DEBIT, "100.00"),
            _entry(acc_id, EntryType.CREDIT, "300.00"),
        ]
        assert calculate_balance(AccountType.ASSET, entries) == Decimal("-200.00")
