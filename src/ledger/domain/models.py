from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from ledger.domain.enums import AccountType, EntryType


@dataclass(frozen=True)
class Account:
    id: UUID
    name: str
    type: AccountType


@dataclass(frozen=True)
class TransactionEntry:
    id: UUID
    transaction_id: UUID
    account_id: UUID
    type: EntryType
    amount: Decimal


@dataclass(frozen=True)
class Transaction:
    id: UUID
    timestamp: datetime
    description: str
    entries: list[TransactionEntry]
