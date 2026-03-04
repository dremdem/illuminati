from decimal import Decimal
from uuid import uuid4

import pytest

from ledger.domain.enums import AccountType, EntryType
from ledger.domain.exceptions import (
    InvalidTransactionError,
    UnbalancedTransactionError,
)
from ledger.domain.models import Account, TransactionEntry
from ledger.domain.services import validate_transaction_entries


def _make_account(account_type: AccountType = AccountType.ASSET) -> Account:
    return Account(id=uuid4(), name="Test", type=account_type)


def _debit(account_id: "uuid4", amount: Decimal | str = "100.00") -> TransactionEntry:  # type: ignore[type-arg]
    return TransactionEntry(
        id=uuid4(),
        transaction_id=uuid4(),
        account_id=account_id,
        type=EntryType.DEBIT,
        amount=Decimal(amount),
    )


def _credit(account_id: "uuid4", amount: Decimal | str = "100.00") -> TransactionEntry:  # type: ignore[type-arg]
    return TransactionEntry(
        id=uuid4(),
        transaction_id=uuid4(),
        account_id=account_id,
        type=EntryType.CREDIT,
        amount=Decimal(amount),
    )


class TestValidTransaction:
    def test_balanced_two_entry_transaction(self) -> None:
        acc1 = _make_account()
        acc2 = _make_account()
        entries = [_debit(acc1.id), _credit(acc2.id)]
        validate_transaction_entries(entries, description="Test")

    def test_balanced_multi_entry_transaction(self) -> None:
        acc1 = _make_account()
        acc2 = _make_account()
        acc3 = _make_account()
        entries = [
            _debit(acc1.id, "60.00"),
            _debit(acc2.id, "40.00"),
            _credit(acc3.id, "100.00"),
        ]
        validate_transaction_entries(entries, description="Multi-entry")


class TestUnbalancedTransaction:
    def test_debits_exceed_credits(self) -> None:
        acc1 = _make_account()
        acc2 = _make_account()
        entries = [_debit(acc1.id, "150.00"), _credit(acc2.id, "100.00")]
        with pytest.raises(UnbalancedTransactionError):
            validate_transaction_entries(entries, description="Unbalanced")

    def test_credits_exceed_debits(self) -> None:
        acc1 = _make_account()
        acc2 = _make_account()
        entries = [_debit(acc1.id, "50.00"), _credit(acc2.id, "100.00")]
        with pytest.raises(UnbalancedTransactionError):
            validate_transaction_entries(entries, description="Unbalanced")


class TestMinimumEntries:
    def test_zero_entries_rejected(self) -> None:
        with pytest.raises(InvalidTransactionError, match="at least 2"):
            validate_transaction_entries([], description="Empty")

    def test_one_entry_rejected(self) -> None:
        acc = _make_account()
        with pytest.raises(InvalidTransactionError, match="at least 2"):
            validate_transaction_entries([_debit(acc.id)], description="Single")


class TestDebitAndCreditRequired:
    def test_only_debits_rejected(self) -> None:
        acc1 = _make_account()
        acc2 = _make_account()
        entries = [_debit(acc1.id), _debit(acc2.id)]
        with pytest.raises(InvalidTransactionError, match="CREDIT"):
            validate_transaction_entries(entries, description="All debits")

    def test_only_credits_rejected(self) -> None:
        acc1 = _make_account()
        acc2 = _make_account()
        entries = [_credit(acc1.id), _credit(acc2.id)]
        with pytest.raises(InvalidTransactionError, match="DEBIT"):
            validate_transaction_entries(entries, description="All credits")


class TestPositiveAmounts:
    def test_zero_amount_rejected(self) -> None:
        acc1 = _make_account()
        acc2 = _make_account()
        entries = [_debit(acc1.id, "0.00"), _credit(acc2.id, "0.00")]
        with pytest.raises(InvalidTransactionError, match="positive"):
            validate_transaction_entries(entries, description="Zero")

    def test_negative_amount_rejected(self) -> None:
        acc1 = _make_account()
        acc2 = _make_account()
        entries = [_debit(acc1.id, "-50.00"), _credit(acc2.id, "-50.00")]
        with pytest.raises(InvalidTransactionError, match="positive"):
            validate_transaction_entries(entries, description="Negative")


class TestDescription:
    def test_empty_description_rejected(self) -> None:
        acc1 = _make_account()
        acc2 = _make_account()
        entries = [_debit(acc1.id), _credit(acc2.id)]
        with pytest.raises(InvalidTransactionError, match="description"):
            validate_transaction_entries(entries, description="")

    def test_whitespace_only_description_rejected(self) -> None:
        acc1 = _make_account()
        acc2 = _make_account()
        entries = [_debit(acc1.id), _credit(acc2.id)]
        with pytest.raises(InvalidTransactionError, match="description"):
            validate_transaction_entries(entries, description="   ")
