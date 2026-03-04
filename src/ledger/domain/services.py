"""Domain services: transaction validation and balance calculation."""

from collections.abc import Sequence
from decimal import Decimal

from ledger.domain.enums import AccountType, EntryType
from ledger.domain.exceptions import (
    InvalidTransactionError,
    UnbalancedTransactionError,
)
from ledger.domain.models import TransactionEntry

DEBIT_NORMAL_TYPES = {AccountType.ASSET, AccountType.EXPENSE}


def validate_transaction_entries(
    entries: Sequence[TransactionEntry],
    description: str,
) -> None:
    """
    Validate transaction entries against double-entry bookkeeping rules.

    :param entries: list of debit/credit entries to validate
    :param description: human-readable transaction description
    :raises InvalidTransactionError: if entries violate structural rules
    :raises UnbalancedTransactionError: if total debits != total credits
    """
    if not description or not description.strip():
        raise InvalidTransactionError("Transaction description must not be empty")

    if len(entries) < 2:
        raise InvalidTransactionError("Transaction must have at least 2 entries")

    for entry in entries:
        if entry.amount <= Decimal("0"):
            raise InvalidTransactionError("All entry amounts must be positive")

    has_debit = any(e.type == EntryType.DEBIT for e in entries)
    has_credit = any(e.type == EntryType.CREDIT for e in entries)

    if not has_debit:
        raise InvalidTransactionError("Transaction must have at least one DEBIT entry")
    if not has_credit:
        raise InvalidTransactionError("Transaction must have at least one CREDIT entry")

    total_debits = sum(
        (e.amount for e in entries if e.type == EntryType.DEBIT), Decimal("0")
    )
    total_credits = sum(
        (e.amount for e in entries if e.type == EntryType.CREDIT), Decimal("0")
    )

    if total_debits != total_credits:
        raise UnbalancedTransactionError(
            f"Total debits ({total_debits}) must equal total credits ({total_credits})"
        )


def calculate_balance(
    account_type: AccountType,
    entries: Sequence[TransactionEntry],
) -> Decimal:
    """
    Compute account balance from transaction entries.

    ASSET and EXPENSE are debit-normal: balance = debits - credits.
    LIABILITY and REVENUE are credit-normal: balance = credits - debits.

    :param account_type: determines balance calculation direction
    :param entries: transaction entries affecting this account
    :return: computed balance as Decimal
    """
    total_debits = sum(
        (e.amount for e in entries if e.type == EntryType.DEBIT), Decimal("0")
    )
    total_credits = sum(
        (e.amount for e in entries if e.type == EntryType.CREDIT), Decimal("0")
    )

    if account_type in DEBIT_NORMAL_TYPES:
        return total_debits - total_credits
    return total_credits - total_debits
