"""Enumerations for account types and transaction entry directions."""

from enum import StrEnum


class AccountType(StrEnum):
    """Financial account classification determining balance calculation direction."""

    ASSET = "ASSET"
    LIABILITY = "LIABILITY"
    REVENUE = "REVENUE"
    EXPENSE = "EXPENSE"


class EntryType(StrEnum):
    """Transaction entry direction: debit or credit."""

    DEBIT = "DEBIT"
    CREDIT = "CREDIT"
