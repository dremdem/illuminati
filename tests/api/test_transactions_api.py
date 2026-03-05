"""API tests for transaction processing endpoints."""

import uuid

import httpx
import pytest


async def _create_account(
    client: httpx.AsyncClient, name: str, account_type: str
) -> str:
    """
    Create an account via the API and return its ID.

    :param client: async HTTP client
    :param name: account name
    :param account_type: account type string
    :return: UUID string of the created account
    """
    resp = await client.post(
        "/api/accounts",
        json={"name": name, "type": account_type},
    )
    return resp.json()["id"]


@pytest.mark.asyncio
async def test_create_transaction_success(client: httpx.AsyncClient) -> None:
    """POST /api/transactions with valid balanced entries returns 201."""
    cash_id = await _create_account(client, "Cash", "ASSET")
    revenue_id = await _create_account(client, "Revenue", "REVENUE")

    response = await client.post(
        "/api/transactions",
        json={
            "description": "Sale of goods",
            "date": "2025-01-15T10:30:00",
            "entries": [
                {"accountId": cash_id, "type": "DEBIT", "amount": 100.00},
                {"accountId": revenue_id, "type": "CREDIT", "amount": 100.00},
            ],
        },
    )

    assert response.status_code == 201
    body = response.json()
    uuid.UUID(body["id"])
    assert body["description"] == "Sale of goods"
    assert body["timestamp"] == "2025-01-15T10:30:00"
    assert len(body["entries"]) == 2

    entries_by_type = {e["type"]: e for e in body["entries"]}
    assert entries_by_type["DEBIT"]["accountId"] == cash_id
    assert entries_by_type["DEBIT"]["amount"] == "100.00"
    assert entries_by_type["CREDIT"]["accountId"] == revenue_id
    assert entries_by_type["CREDIT"]["amount"] == "100.00"


@pytest.mark.asyncio
async def test_create_transaction_unbalanced(client: httpx.AsyncClient) -> None:
    """POST /api/transactions with unbalanced entries returns 400."""
    cash_id = await _create_account(client, "Cash", "ASSET")
    revenue_id = await _create_account(client, "Revenue", "REVENUE")

    response = await client.post(
        "/api/transactions",
        json={
            "description": "Unbalanced",
            "date": "2025-01-15T10:30:00",
            "entries": [
                {"accountId": cash_id, "type": "DEBIT", "amount": 100.00},
                {"accountId": revenue_id, "type": "CREDIT", "amount": 50.00},
            ],
        },
    )

    assert response.status_code == 400
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_create_transaction_fewer_than_two_entries(
    client: httpx.AsyncClient,
) -> None:
    """POST /api/transactions with fewer than 2 entries returns 400."""
    cash_id = await _create_account(client, "Cash", "ASSET")

    response = await client.post(
        "/api/transactions",
        json={
            "description": "Single entry",
            "date": "2025-01-15T10:30:00",
            "entries": [
                {"accountId": cash_id, "type": "DEBIT", "amount": 100.00},
            ],
        },
    )

    assert response.status_code == 400
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_create_transaction_only_debits_no_credits(
    client: httpx.AsyncClient,
) -> None:
    """POST /api/transactions with only debits (no credits) returns 400."""
    cash_id = await _create_account(client, "Cash", "ASSET")
    supplies_id = await _create_account(client, "Supplies", "EXPENSE")

    response = await client.post(
        "/api/transactions",
        json={
            "description": "Only debits",
            "date": "2025-01-15T10:30:00",
            "entries": [
                {"accountId": cash_id, "type": "DEBIT", "amount": 50.00},
                {"accountId": supplies_id, "type": "DEBIT", "amount": 50.00},
            ],
        },
    )

    assert response.status_code == 400
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_create_transaction_nonexistent_account(
    client: httpx.AsyncClient,
) -> None:
    """POST /api/transactions with a non-existent account ID returns 404."""
    cash_id = await _create_account(client, "Cash", "ASSET")
    fake_id = str(uuid.uuid4())

    response = await client.post(
        "/api/transactions",
        json={
            "description": "Ghost account",
            "date": "2025-01-15T10:30:00",
            "entries": [
                {"accountId": cash_id, "type": "DEBIT", "amount": 100.00},
                {"accountId": fake_id, "type": "CREDIT", "amount": 100.00},
            ],
        },
    )

    assert response.status_code == 404
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_create_transaction_negative_amount(
    client: httpx.AsyncClient,
) -> None:
    """POST /api/transactions with a negative amount returns 400."""
    cash_id = await _create_account(client, "Cash", "ASSET")
    revenue_id = await _create_account(client, "Revenue", "REVENUE")

    response = await client.post(
        "/api/transactions",
        json={
            "description": "Negative amount",
            "date": "2025-01-15T10:30:00",
            "entries": [
                {"accountId": cash_id, "type": "DEBIT", "amount": -100.00},
                {"accountId": revenue_id, "type": "CREDIT", "amount": -100.00},
            ],
        },
    )

    assert response.status_code == 400
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_create_transaction_zero_amount(
    client: httpx.AsyncClient,
) -> None:
    """POST /api/transactions with a zero amount returns 400."""
    cash_id = await _create_account(client, "Cash", "ASSET")
    revenue_id = await _create_account(client, "Revenue", "REVENUE")

    response = await client.post(
        "/api/transactions",
        json={
            "description": "Zero amount",
            "date": "2025-01-15T10:30:00",
            "entries": [
                {"accountId": cash_id, "type": "DEBIT", "amount": 0},
                {"accountId": revenue_id, "type": "CREDIT", "amount": 0},
            ],
        },
    )

    assert response.status_code == 400
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_create_transaction_empty_description(
    client: httpx.AsyncClient,
) -> None:
    """POST /api/transactions with an empty description returns 400."""
    cash_id = await _create_account(client, "Cash", "ASSET")
    revenue_id = await _create_account(client, "Revenue", "REVENUE")

    response = await client.post(
        "/api/transactions",
        json={
            "description": "   ",
            "date": "2025-01-15T10:30:00",
            "entries": [
                {"accountId": cash_id, "type": "DEBIT", "amount": 100.00},
                {"accountId": revenue_id, "type": "CREDIT", "amount": 100.00},
            ],
        },
    )

    assert response.status_code == 400
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_get_transaction_by_id(client: httpx.AsyncClient) -> None:
    """GET /api/transactions/{id} returns the correct transaction."""
    cash_id = await _create_account(client, "Cash", "ASSET")
    revenue_id = await _create_account(client, "Revenue", "REVENUE")

    create_resp = await client.post(
        "/api/transactions",
        json={
            "description": "Sale",
            "date": "2025-02-01T12:00:00",
            "entries": [
                {"accountId": cash_id, "type": "DEBIT", "amount": 250.00},
                {"accountId": revenue_id, "type": "CREDIT", "amount": 250.00},
            ],
        },
    )
    txn_id = create_resp.json()["id"]

    response = await client.get(f"/api/transactions/{txn_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == txn_id
    assert body["description"] == "Sale"
    assert len(body["entries"]) == 2


@pytest.mark.asyncio
async def test_get_transaction_not_found(client: httpx.AsyncClient) -> None:
    """GET /api/transactions/{id} with non-existent ID returns 404."""
    fake_id = uuid.uuid4()
    response = await client.get(f"/api/transactions/{fake_id}")

    assert response.status_code == 404
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_get_transactions_for_account(client: httpx.AsyncClient) -> None:
    """GET /api/accounts/{id}/transactions returns transactions for account."""
    cash_id = await _create_account(client, "Cash", "ASSET")
    revenue_id = await _create_account(client, "Revenue", "REVENUE")

    await client.post(
        "/api/transactions",
        json={
            "description": "First sale",
            "date": "2025-01-01T10:00:00",
            "entries": [
                {"accountId": cash_id, "type": "DEBIT", "amount": 100.00},
                {"accountId": revenue_id, "type": "CREDIT", "amount": 100.00},
            ],
        },
    )
    await client.post(
        "/api/transactions",
        json={
            "description": "Second sale",
            "date": "2025-01-02T10:00:00",
            "entries": [
                {"accountId": cash_id, "type": "DEBIT", "amount": 200.00},
                {"accountId": revenue_id, "type": "CREDIT", "amount": 200.00},
            ],
        },
    )

    response = await client.get(f"/api/accounts/{cash_id}/transactions")

    assert response.status_code == 200
    txns = response.json()
    assert len(txns) == 2
    descriptions = {t["description"] for t in txns}
    assert descriptions == {"First sale", "Second sale"}


@pytest.mark.asyncio
async def test_get_transactions_for_nonexistent_account(
    client: httpx.AsyncClient,
) -> None:
    """GET /api/accounts/{id}/transactions with non-existent account returns 404."""
    fake_id = uuid.uuid4()
    response = await client.get(f"/api/accounts/{fake_id}/transactions")

    assert response.status_code == 404
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_get_account_transactions_with_limit(
    client: httpx.AsyncClient,
) -> None:
    """GET /api/accounts/{id}/transactions?limit=1 returns at most 1 transaction."""
    cash_id = await _create_account(client, "Cash", "ASSET")
    revenue_id = await _create_account(client, "Revenue", "REVENUE")

    for i in range(3):
        await client.post(
            "/api/transactions",
            json={
                "description": f"Sale {i + 1}",
                "date": f"2025-01-0{i + 1}T10:00:00",
                "entries": [
                    {"accountId": cash_id, "type": "DEBIT", "amount": 100.00},
                    {"accountId": revenue_id, "type": "CREDIT", "amount": 100.00},
                ],
            },
        )

    response = await client.get(
        f"/api/accounts/{cash_id}/transactions", params={"limit": 1}
    )

    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.asyncio
async def test_get_account_transactions_with_offset(
    client: httpx.AsyncClient,
) -> None:
    """GET /api/accounts/{id}/transactions?offset=1 skips the first transaction."""
    cash_id = await _create_account(client, "Cash", "ASSET")
    revenue_id = await _create_account(client, "Revenue", "REVENUE")

    for i in range(3):
        await client.post(
            "/api/transactions",
            json={
                "description": f"Sale {i + 1}",
                "date": f"2025-01-0{i + 1}T10:00:00",
                "entries": [
                    {"accountId": cash_id, "type": "DEBIT", "amount": 100.00},
                    {"accountId": revenue_id, "type": "CREDIT", "amount": 100.00},
                ],
            },
        )

    response = await client.get(
        f"/api/accounts/{cash_id}/transactions", params={"offset": 1}
    )

    assert response.status_code == 200
    assert len(response.json()) == 2


@pytest.mark.asyncio
async def test_get_account_transactions_with_from_date(
    client: httpx.AsyncClient,
) -> None:
    """from_date query param excludes earlier transactions."""
    cash_id = await _create_account(client, "Cash", "ASSET")
    revenue_id = await _create_account(client, "Revenue", "REVENUE")

    for i in range(3):
        await client.post(
            "/api/transactions",
            json={
                "description": f"Sale {i + 1}",
                "date": f"2025-01-0{i + 1}T10:00:00",
                "entries": [
                    {"accountId": cash_id, "type": "DEBIT", "amount": 100.00},
                    {"accountId": revenue_id, "type": "CREDIT", "amount": 100.00},
                ],
            },
        )

    response = await client.get(
        f"/api/accounts/{cash_id}/transactions",
        params={"from_date": "2025-01-02T00:00:00"},
    )

    assert response.status_code == 200
    txns = response.json()
    assert len(txns) == 2
    descriptions = {t["description"] for t in txns}
    assert "Sale 1" not in descriptions


@pytest.mark.asyncio
async def test_get_account_transactions_with_to_date(
    client: httpx.AsyncClient,
) -> None:
    """GET /api/accounts/{id}/transactions?to_date=... excludes later transactions."""
    cash_id = await _create_account(client, "Cash", "ASSET")
    revenue_id = await _create_account(client, "Revenue", "REVENUE")

    for i in range(3):
        await client.post(
            "/api/transactions",
            json={
                "description": f"Sale {i + 1}",
                "date": f"2025-01-0{i + 1}T10:00:00",
                "entries": [
                    {"accountId": cash_id, "type": "DEBIT", "amount": 100.00},
                    {"accountId": revenue_id, "type": "CREDIT", "amount": 100.00},
                ],
            },
        )

    response = await client.get(
        f"/api/accounts/{cash_id}/transactions",
        params={"to_date": "2025-01-02T23:59:59"},
    )

    assert response.status_code == 200
    txns = response.json()
    assert len(txns) == 2
    descriptions = {t["description"] for t in txns}
    assert "Sale 3" not in descriptions


@pytest.mark.asyncio
async def test_get_account_transactions_with_date_range(
    client: httpx.AsyncClient,
) -> None:
    """from_date + to_date returns only transactions in range."""
    cash_id = await _create_account(client, "Cash", "ASSET")
    revenue_id = await _create_account(client, "Revenue", "REVENUE")

    for i in range(5):
        await client.post(
            "/api/transactions",
            json={
                "description": f"Sale {i + 1}",
                "date": f"2025-01-0{i + 1}T10:00:00",
                "entries": [
                    {"accountId": cash_id, "type": "DEBIT", "amount": 100.00},
                    {"accountId": revenue_id, "type": "CREDIT", "amount": 100.00},
                ],
            },
        )

    response = await client.get(
        f"/api/accounts/{cash_id}/transactions",
        params={
            "from_date": "2025-01-02T00:00:00",
            "to_date": "2025-01-04T23:59:59",
        },
    )

    assert response.status_code == 200
    txns = response.json()
    assert len(txns) == 3
    descriptions = {t["description"] for t in txns}
    assert descriptions == {"Sale 2", "Sale 3", "Sale 4"}
