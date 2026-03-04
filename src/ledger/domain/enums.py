"""Enumerations for account types and transaction entry directions."""

import enum


class AccountType(enum.StrEnum):
    """Financial account classification determining balance calculation direction."""

    ASSET = "ASSET"
    LIABILITY = "LIABILITY"
    REVENUE = "REVENUE"
    EXPENSE = "EXPENSE"


class EntryType(enum.StrEnum):
    """Transaction entry direction: debit or credit."""

    DEBIT = "DEBIT"
    CREDIT = "CREDIT"
