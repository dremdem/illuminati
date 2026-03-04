"""Pydantic v2 request/response models for the Account API."""

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
