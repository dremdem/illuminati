"""API tests for account management endpoints."""

import datetime
import uuid

import httpx
import pytest
import sqlalchemy.ext.asyncio as sa_async

import ledger.domain.enums as enums
import ledger.domain.models as models
import ledger.infrastructure.mappers as mappers
import ledger.infrastructure.models as orm_models


@pytest.mark.asyncio
async def test_create_account_success(client: httpx.AsyncClient) -> None:
    """POST /api/accounts with valid data returns 201 and correct body."""
    response = await client.post(
        "/api/accounts",
        json={"name": "Cash", "type": "ASSET"},
    )

    assert response.status_code == 201
    body = response.json()
    uuid.UUID(body["id"])  # validates it's a proper UUID
    assert body["name"] == "Cash"
    assert body["type"] == "ASSET"
    assert body["balance"] == "0.00"


@pytest.mark.asyncio
async def test_create_account_duplicate_name(client: httpx.AsyncClient) -> None:
    """POST /api/accounts with a duplicate name returns 409."""
    await client.post(
        "/api/accounts",
        json={"name": "Revenue", "type": "REVENUE"},
    )
    response = await client.post(
        "/api/accounts",
        json={"name": "Revenue", "type": "REVENUE"},
    )

    assert response.status_code == 409
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_create_account_empty_name(client: httpx.AsyncClient) -> None:
    """POST /api/accounts with empty name returns 400 (business rule)."""
    response = await client.post(
        "/api/accounts",
        json={"name": "   ", "type": "ASSET"},
    )

    assert response.status_code == 400
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_create_account_invalid_type(client: httpx.AsyncClient) -> None:
    """POST /api/accounts with invalid type returns 422 (Pydantic validation)."""
    response = await client.post(
        "/api/accounts",
        json={"name": "Bad", "type": "INVALID"},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_all_accounts_empty(client: httpx.AsyncClient) -> None:
    """GET /api/accounts with no data returns 200 and empty list."""
    response = await client.get("/api/accounts")

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_all_accounts_with_balances(
    client: httpx.AsyncClient,
    db_session: sa_async.AsyncSession,
) -> None:
    """GET /api/accounts returns accounts with computed balances."""
    cash = models.Account(id=uuid.uuid4(), name="Cash", type=enums.AccountType.ASSET)
    revenue = models.Account(
        id=uuid.uuid4(), name="Revenue", type=enums.AccountType.REVENUE
    )
    db_session.add(mappers.account_to_orm(cash))
    db_session.add(mappers.account_to_orm(revenue))
    await db_session.flush()

    # Create a transaction: debit Cash $100, credit Revenue $100
    txn_id = uuid.uuid4()
    orm_txn = orm_models.TransactionModel(
        id=txn_id,
        timestamp=datetime.datetime(2025, 1, 1, tzinfo=datetime.UTC),
        description="Sale",
    )
    db_session.add(orm_txn)
    await db_session.flush()

    db_session.add(
        orm_models.TransactionEntryModel(
            id=uuid.uuid4(),
            transaction_id=txn_id,
            account_id=cash.id,
            entry_type="DEBIT",
            amount=100,
        )
    )
    db_session.add(
        orm_models.TransactionEntryModel(
            id=uuid.uuid4(),
            transaction_id=txn_id,
            account_id=revenue.id,
            entry_type="CREDIT",
            amount=100,
        )
    )
    await db_session.flush()

    response = await client.get("/api/accounts")

    assert response.status_code == 200
    accounts = response.json()
    assert len(accounts) == 2

    accounts_by_name = {a["name"]: a for a in accounts}
    assert accounts_by_name["Cash"]["balance"] == "100.00"
    assert accounts_by_name["Revenue"]["balance"] == "100.00"


@pytest.mark.asyncio
async def test_get_account_by_id(client: httpx.AsyncClient) -> None:
    """GET /api/accounts/{id} returns the correct account with balance."""
    create_resp = await client.post(
        "/api/accounts",
        json={"name": "Expenses", "type": "EXPENSE"},
    )
    account_id = create_resp.json()["id"]

    response = await client.get(f"/api/accounts/{account_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == account_id
    assert body["name"] == "Expenses"
    assert body["type"] == "EXPENSE"
    assert body["balance"] == "0.00"


@pytest.mark.asyncio
async def test_get_account_not_found(client: httpx.AsyncClient) -> None:
    """GET /api/accounts/{id} with non-existent ID returns 404."""
    fake_id = uuid.uuid4()
    response = await client.get(f"/api/accounts/{fake_id}")

    assert response.status_code == 404
    assert "detail" in response.json()
