"""Pydantic v2 request/response models for the Account and Transaction APIs."""

import datetime
import decimal

import pydantic

import ledger.domain.enums as enums


class CreateAccountRequest(pydantic.BaseModel):
    """Request body for creating a new account."""

    name: str
    type: enums.AccountType


class AccountResponse(pydantic.BaseModel):
    """Response body representing an account with its computed balance."""

    id: str
    name: str
    type: enums.AccountType
    balance: str


class TransactionEntryRequest(pydantic.BaseModel):
    """A single entry within a create-transaction request."""

    model_config = pydantic.ConfigDict(populate_by_name=True)

    account_id: str = pydantic.Field(alias="accountId")
    type: enums.EntryType
    amount: decimal.Decimal


class CreateTransactionRequest(pydantic.BaseModel):
    """Request body for creating a new transaction."""

    model_config = pydantic.ConfigDict(populate_by_name=True)

    description: str
    timestamp: datetime.datetime = pydantic.Field(alias="date")
    entries: list[TransactionEntryRequest]


class TransactionEntryResponse(pydantic.BaseModel):
    """Response body for a single transaction entry."""

    model_config = pydantic.ConfigDict(populate_by_name=True)

    id: str
    account_id: str = pydantic.Field(alias="accountId")
    type: enums.EntryType
    amount: str


class TransactionResponse(pydantic.BaseModel):
    """Response body representing a transaction with its entries."""

    id: str
    description: str
    timestamp: str
    entries: list[TransactionEntryResponse]
