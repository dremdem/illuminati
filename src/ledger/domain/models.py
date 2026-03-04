from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from ledger.domain.enums import AccountType, EntryType


@dataclass(frozen=True)
class Account:
    """Financial account (e.g., Cash, Revenue). Balance is computed, never stored."""

    id: UUID
    name: str
    type: AccountType


@dataclass(frozen=True)
class TransactionEntry:
    """A single debit or credit leg within a transaction."""

    id: UUID
    transaction_id: UUID
    account_id: UUID
    type: EntryType
    amount: Decimal


@dataclass(frozen=True)
class Transaction:
    """A financial event moving money between accounts via balanced entries."""

    id: UUID
    timestamp: datetime
    description: str
    entries: list[TransactionEntry]
