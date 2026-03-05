"""Pydantic v2 request/response models for the Account and Transaction APIs."""

import datetime
import decimal

import pydantic

import ledger.domain.enums as enums


class CreateAccountRequest(pydantic.BaseModel):
    """Request body for creating a new account."""

    name: str = pydantic.Field(description="Unique display name for the account.")
    type: enums.AccountType = pydantic.Field(
        description="Financial classification: ASSET, LIABILITY, REVENUE, or EXPENSE."
    )


class AccountResponse(pydantic.BaseModel):
    """Response body representing an account with its computed balance."""

    id: str = pydantic.Field(description="Unique account identifier (UUID).")
    name: str = pydantic.Field(description="Account display name.")
    type: enums.AccountType = pydantic.Field(
        description="Financial classification: ASSET, LIABILITY, REVENUE, or EXPENSE."
    )
    balance: str = pydantic.Field(
        description="Current balance computed from all transaction "
        "entries (e.g. '1350.00')."
    )


class TransactionEntryRequest(pydantic.BaseModel):
    """A single entry within a create-transaction request."""

    model_config = pydantic.ConfigDict(populate_by_name=True)

    account_id: str = pydantic.Field(
        alias="accountId",
        description="UUID of the account this entry affects.",
    )
    type: enums.EntryType = pydantic.Field(description="Entry type: DEBIT or CREDIT.")
    amount: decimal.Decimal = pydantic.Field(
        description="Positive monetary amount (e.g. 100.00)."
    )


class CreateTransactionRequest(pydantic.BaseModel):
    """Request body for creating a new transaction."""

    model_config = pydantic.ConfigDict(populate_by_name=True)

    description: str = pydantic.Field(
        description="Human-readable description of the transaction."
    )
    timestamp: datetime.datetime = pydantic.Field(
        alias="date",
        description="When the transaction occurred (ISO 8601).",
    )
    entries: list[TransactionEntryRequest] = pydantic.Field(
        description="Debit and credit entries (minimum 2, must balance)."
    )


class TransactionEntryResponse(pydantic.BaseModel):
    """Response body for a single transaction entry."""

    model_config = pydantic.ConfigDict(populate_by_name=True)

    id: str = pydantic.Field(description="Unique entry identifier (UUID).")
    account_id: str = pydantic.Field(
        alias="accountId",
        description="UUID of the account this entry affects.",
    )
    type: enums.EntryType = pydantic.Field(description="Entry type: DEBIT or CREDIT.")
    amount: str = pydantic.Field(
        description="Monetary amount as a string with 2 decimal places."
    )


class TransactionResponse(pydantic.BaseModel):
    """Response body representing a transaction with its entries."""

    id: str = pydantic.Field(description="Unique transaction identifier (UUID).")
    description: str = pydantic.Field(
        description="Human-readable description of the transaction."
    )
    timestamp: str = pydantic.Field(
        description="When the transaction occurred (ISO 8601)."
    )
    entries: list[TransactionEntryResponse] = pydantic.Field(
        description="All debit and credit entries for this transaction."
    )


class PaginatedAccountResponse(pydantic.BaseModel):
    """Paginated envelope for account list responses."""

    items: list[AccountResponse] = pydantic.Field(
        description="Page of account results."
    )
    total: int = pydantic.Field(
        description="Total number of accounts (ignoring limit/offset)."
    )
    limit: int | None = pydantic.Field(
        description="Maximum number of items requested (None = all)."
    )
    offset: int = pydantic.Field(description="Number of items skipped.")


class PaginatedTransactionResponse(pydantic.BaseModel):
    """Paginated envelope for transaction list responses."""

    items: list[TransactionResponse] = pydantic.Field(
        description="Page of transaction results."
    )
    total: int = pydantic.Field(
        description="Total number of transactions (ignoring limit/offset)."
    )
    limit: int | None = pydantic.Field(
        description="Maximum number of items requested (None = all)."
    )
    offset: int = pydantic.Field(description="Number of items skipped.")
