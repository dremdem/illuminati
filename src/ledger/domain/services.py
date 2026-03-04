"""Domain services: transaction validation and balance calculation."""

import collections.abc
import decimal

import ledger.domain.enums as enums
import ledger.domain.exceptions as exceptions
import ledger.domain.models as models

DEBIT_NORMAL_TYPES = {enums.AccountType.ASSET, enums.AccountType.EXPENSE}


def validate_transaction_entries(
    entries: collections.abc.Sequence[models.TransactionEntry],
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
        raise exceptions.InvalidTransactionError(
            "Transaction description must not be empty"
        )

    if len(entries) < 2:
        raise exceptions.InvalidTransactionError(
            "Transaction must have at least 2 entries"
        )

    for entry in entries:
        if entry.amount <= decimal.Decimal("0"):
            raise exceptions.InvalidTransactionError(
                "All entry amounts must be positive"
            )

    has_debit = any(e.type == enums.EntryType.DEBIT for e in entries)
    has_credit = any(e.type == enums.EntryType.CREDIT for e in entries)

    if not has_debit:
        raise exceptions.InvalidTransactionError(
            "Transaction must have at least one DEBIT entry"
        )
    if not has_credit:
        raise exceptions.InvalidTransactionError(
            "Transaction must have at least one CREDIT entry"
        )

    total_debits = sum(
        (e.amount for e in entries if e.type == enums.EntryType.DEBIT),
        decimal.Decimal("0"),
    )
    total_credits = sum(
        (e.amount for e in entries if e.type == enums.EntryType.CREDIT),
        decimal.Decimal("0"),
    )

    if total_debits != total_credits:
        raise exceptions.UnbalancedTransactionError(
            f"Total debits ({total_debits}) must equal total credits ({total_credits})"
        )


def calculate_balance(
    account_type: enums.AccountType,
    entries: collections.abc.Sequence[models.TransactionEntry],
) -> decimal.Decimal:
    """
    Compute account balance from transaction entries.

    ASSET and EXPENSE are debit-normal: balance = debits - credits.
    LIABILITY and REVENUE are credit-normal: balance = credits - debits.

    :param account_type: determines balance calculation direction
    :param entries: transaction entries affecting this account
    :return: computed balance as Decimal
    """
    total_debits = sum(
        (e.amount for e in entries if e.type == enums.EntryType.DEBIT),
        decimal.Decimal("0"),
    )
    total_credits = sum(
        (e.amount for e in entries if e.type == enums.EntryType.CREDIT),
        decimal.Decimal("0"),
    )

    if account_type in DEBIT_NORMAL_TYPES:
        return total_debits - total_credits
    else:
        return total_credits - total_debits
