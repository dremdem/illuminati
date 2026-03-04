"""Unit tests for transaction validation rules (double-entry bookkeeping)."""

import decimal
import uuid

import pytest

import ledger.domain.enums as enums
import ledger.domain.exceptions as exceptions
import ledger.domain.models as models
import ledger.domain.services as services


def _make_account(
    account_type: enums.AccountType = enums.AccountType.ASSET,
) -> models.Account:
    """Create a test account with the given type."""
    return models.Account(id=uuid.uuid4(), name="Test", type=account_type)


def _debit(
    account_id: uuid.UUID,
    amount: str = "100.00",
) -> models.TransactionEntry:
    """Create a DEBIT entry for testing."""
    return models.TransactionEntry(
        id=uuid.uuid4(),
        transaction_id=uuid.uuid4(),
        account_id=account_id,
        type=enums.EntryType.DEBIT,
        amount=decimal.Decimal(amount),
    )


def _credit(
    account_id: uuid.UUID,
    amount: str = "100.00",
) -> models.TransactionEntry:
    """Create a CREDIT entry for testing."""
    return models.TransactionEntry(
        id=uuid.uuid4(),
        transaction_id=uuid.uuid4(),
        account_id=account_id,
        type=enums.EntryType.CREDIT,
        amount=decimal.Decimal(amount),
    )


class TestValidTransaction:
    """Tests for valid, balanced transactions."""

    def test_balanced_two_entry_transaction(self) -> None:
        """Verify a simple balanced transaction passes validation."""
        acc1 = _make_account()
        acc2 = _make_account()
        entries = [_debit(acc1.id), _credit(acc2.id)]
        services.validate_transaction_entries(entries, description="Test")

    def test_balanced_multi_entry_transaction(self) -> None:
        """Verify a multi-entry balanced transaction passes."""
        acc1 = _make_account()
        acc2 = _make_account()
        acc3 = _make_account()
        entries = [
            _debit(acc1.id, "60.00"),
            _debit(acc2.id, "40.00"),
            _credit(acc3.id, "100.00"),
        ]
        services.validate_transaction_entries(entries, description="Multi-entry")


class TestUnbalancedTransaction:
    """Tests for transactions where debits != credits."""

    def test_debits_exceed_credits(self) -> None:
        """Verify rejection when debits > credits."""
        acc1 = _make_account()
        acc2 = _make_account()
        entries = [_debit(acc1.id, "150.00"), _credit(acc2.id, "100.00")]
        with pytest.raises(exceptions.UnbalancedTransactionError):
            services.validate_transaction_entries(entries, description="Unbalanced")

    def test_credits_exceed_debits(self) -> None:
        """Verify rejection when credits > debits."""
        acc1 = _make_account()
        acc2 = _make_account()
        entries = [_debit(acc1.id, "50.00"), _credit(acc2.id, "100.00")]
        with pytest.raises(exceptions.UnbalancedTransactionError):
            services.validate_transaction_entries(entries, description="Unbalanced")


class TestMinimumEntries:
    """Tests for minimum entry count requirement."""

    def test_zero_entries_rejected(self) -> None:
        """Verify rejection with no entries."""
        with pytest.raises(exceptions.InvalidTransactionError, match="at least 2"):
            services.validate_transaction_entries([], description="Empty")

    def test_one_entry_rejected(self) -> None:
        """Verify rejection with only one entry."""
        acc = _make_account()
        with pytest.raises(exceptions.InvalidTransactionError, match="at least 2"):
            services.validate_transaction_entries(
                [_debit(acc.id)], description="Single"
            )


class TestDebitAndCreditRequired:
    """Tests for requiring both debit and credit entries."""

    def test_only_debits_rejected(self) -> None:
        """Verify rejection when all entries are debits."""
        acc1 = _make_account()
        acc2 = _make_account()
        entries = [_debit(acc1.id), _debit(acc2.id)]
        with pytest.raises(exceptions.InvalidTransactionError, match="CREDIT"):
            services.validate_transaction_entries(entries, description="All debits")

    def test_only_credits_rejected(self) -> None:
        """Verify rejection when all entries are credits."""
        acc1 = _make_account()
        acc2 = _make_account()
        entries = [_credit(acc1.id), _credit(acc2.id)]
        with pytest.raises(exceptions.InvalidTransactionError, match="DEBIT"):
            services.validate_transaction_entries(entries, description="All credits")


class TestPositiveAmounts:
    """Tests for positive amount requirement."""

    def test_zero_amount_rejected(self) -> None:
        """Verify rejection of zero-amount entries."""
        acc1 = _make_account()
        acc2 = _make_account()
        entries = [_debit(acc1.id, "0.00"), _credit(acc2.id, "0.00")]
        with pytest.raises(exceptions.InvalidTransactionError, match="positive"):
            services.validate_transaction_entries(entries, description="Zero")

    def test_negative_amount_rejected(self) -> None:
        """Verify rejection of negative-amount entries."""
        acc1 = _make_account()
        acc2 = _make_account()
        entries = [_debit(acc1.id, "-50.00"), _credit(acc2.id, "-50.00")]
        with pytest.raises(exceptions.InvalidTransactionError, match="positive"):
            services.validate_transaction_entries(entries, description="Negative")


class TestDescription:
    """Tests for non-empty description requirement."""

    def test_empty_description_rejected(self) -> None:
        """Verify rejection of empty description."""
        acc1 = _make_account()
        acc2 = _make_account()
        entries = [_debit(acc1.id), _credit(acc2.id)]
        with pytest.raises(exceptions.InvalidTransactionError, match="description"):
            services.validate_transaction_entries(entries, description="")

    def test_whitespace_only_description_rejected(self) -> None:
        """Verify rejection of whitespace-only description."""
        acc1 = _make_account()
        acc2 = _make_account()
        entries = [_debit(acc1.id), _credit(acc2.id)]
        with pytest.raises(exceptions.InvalidTransactionError, match="description"):
            services.validate_transaction_entries(entries, description="   ")
