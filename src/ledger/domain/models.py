"""Domain entities: Account, Transaction, and TransactionEntry."""

import dataclasses
import datetime
import decimal
import uuid

import ledger.domain.enums as enums


@dataclasses.dataclass(frozen=True)
class Account:
    """Financial account (e.g., Cash, Revenue). Balance is computed, never stored."""

    id: uuid.UUID
    name: str
    type: enums.AccountType


@dataclasses.dataclass(frozen=True)
class TransactionEntry:
    """A single debit or credit leg within a transaction."""

    id: uuid.UUID
    transaction_id: uuid.UUID
    account_id: uuid.UUID
    type: enums.EntryType
    amount: decimal.Decimal


@dataclasses.dataclass(frozen=True)
class Transaction:
    """A financial event moving money between accounts via balanced entries."""

    id: uuid.UUID
    timestamp: datetime.datetime
    description: str
    entries: list[TransactionEntry]
