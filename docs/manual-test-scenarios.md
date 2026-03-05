# Manual Test Scenarios

Step-by-step test cases for verifying the Financial Ledger API. Every step has a copy-pasteable command and expected output. IDs flow automatically between steps via shell variables.

## Table of Contents

- [Prerequisites](#prerequisites)
- [0. Health Check](#0-health-check)
- [1. Account Management](#1-account-management)
  - [1.1 Create Account — Success](#11-create-account--success)
  - [1.2 Create Account — Duplicate Name (409)](#12-create-account--duplicate-name-409)
  - [1.3 Create Account — Empty Name (400)](#13-create-account--empty-name-400)
  - [1.4 Create Account — Invalid Type (422)](#14-create-account--invalid-type-422)
  - [1.5 Get Account by ID](#15-get-account-by-id)
  - [1.6 Get Account — Not Found (404)](#16-get-account--not-found-404)
  - [1.7 List All Accounts](#17-list-all-accounts)
- [2. Transaction Processing](#2-transaction-processing)
  - [2.1 Create Transaction — Success](#21-create-transaction--success)
  - [2.2 Fewer Than 2 Entries (400)](#22-fewer-than-2-entries-400)
  - [2.3 All Same Type — No CREDIT (400)](#23-all-same-type--no-credit-400)
  - [2.4 Unbalanced Transaction (400)](#24-unbalanced-transaction-400)
  - [2.5 Non-Existent Account in Entry (404)](#25-non-existent-account-in-entry-404)
  - [2.6 Negative Amount (400)](#26-negative-amount-400)
  - [2.7 Zero Amount (400)](#27-zero-amount-400)
  - [2.8 Empty Description (400)](#28-empty-description-400)
  - [2.9 Get Transaction by ID](#29-get-transaction-by-id)
  - [2.10 Get Transaction — Not Found (404)](#210-get-transaction--not-found-404)
- [3. Transaction Listing and Filtering](#3-transaction-listing-and-filtering)
  - [3.1 List All Transactions](#31-list-all-transactions)
  - [3.2 Pagination](#32-pagination)
  - [3.3 Date Range Filter](#33-date-range-filter)
  - [3.4 Transactions for Account](#34-transactions-for-account)
  - [3.5 Transactions for Non-Existent Account (404)](#35-transactions-for-non-existent-account-404)
- [4. Balance Calculation (Double-Entry Rules)](#4-balance-calculation-double-entry-rules)
  - [4.1 Seed Data and Verify Balances](#41-seed-data-and-verify-balances)
  - [4.2 Balance Rules by Account Type](#42-balance-rules-by-account-type)
  - [4.3 Accounting Equation Check](#43-accounting-equation-check)
- [Related Documents](#related-documents)

---

## Prerequisites

Start the services and reset the database to a clean state:

```bash
make up
make db-reset
```

Confirm the API is running:

```bash
curl -s http://localhost:8000/health
```

Expected: `{"status":"ok"}`

> **Requires `jq`** — all commands below use [`jq`](https://jqlang.github.io/jq/) for JSON parsing. Install via `brew install jq` (macOS) or `apt-get install jq` (Debian/Ubuntu).

---

## 0. Health Check

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health
```

Expected: `200`

---

## 1. Account Management

### 1.1 Create Account — Success

```bash
response=$(curl -s -w "\n%{http_code}" -X POST http://localhost:8000/api/accounts \
  -H "Content-Type: application/json" \
  -d '{"name": "Cash", "type": "ASSET"}')
body=$(echo "$response" | sed \$d)
echo "$body" | jq .
echo "→ HTTP $(echo "$response" | tail -1)"
CASH_ID=$(echo "$body" | jq -r '.id')
echo "→ CASH_ID=$CASH_ID"
```

Expected: **HTTP 201**. Response body:

```json
{
  "id": "<uuid>",
  "name": "Cash",
  "type": "ASSET",
  "balance": "0.00"
}
```

Create a second account for transaction tests:

```bash
response=$(curl -s -w "\n%{http_code}" -X POST http://localhost:8000/api/accounts \
  -H "Content-Type: application/json" \
  -d '{"name": "Office Supplies", "type": "EXPENSE"}')
body=$(echo "$response" | sed \$d)
echo "$body" | jq .
echo "→ HTTP $(echo "$response" | tail -1)"
SUPPLIES_ID=$(echo "$body" | jq -r '.id')
echo "→ SUPPLIES_ID=$SUPPLIES_ID"
```

Expected: **HTTP 201** with `balance: "0.00"`.

### 1.2 Create Account — Duplicate Name (409)

```bash
response=$(curl -s -w "\n%{http_code}" -X POST http://localhost:8000/api/accounts \
  -H "Content-Type: application/json" \
  -d '{"name": "Cash", "type": "ASSET"}')
echo "$response" | sed \$d | jq .
echo "→ HTTP $(echo "$response" | tail -1)"
```

Expected: **HTTP 409**. Body contains `"detail"` explaining the duplicate.

### 1.3 Create Account — Empty Name (400)

```bash
response=$(curl -s -w "\n%{http_code}" -X POST http://localhost:8000/api/accounts \
  -H "Content-Type: application/json" \
  -d '{"name": "", "type": "ASSET"}')
echo "$response" | sed \$d | jq .
echo "→ HTTP $(echo "$response" | tail -1)"
```

Expected: **HTTP 400**. Empty name is rejected.

### 1.4 Create Account — Invalid Type (422)

```bash
response=$(curl -s -w "\n%{http_code}" -X POST http://localhost:8000/api/accounts \
  -H "Content-Type: application/json" \
  -d '{"name": "BadType", "type": "FOO"}')
echo "$response" | sed \$d | jq .
echo "→ HTTP $(echo "$response" | tail -1)"
```

Expected: **HTTP 422**. Pydantic rejects the invalid enum value.

### 1.5 Get Account by ID

Using `CASH_ID` from [step 1.1](#11-create-account--success):

```bash
curl -s "http://localhost:8000/api/accounts/$CASH_ID" | jq .
```

Expected: **HTTP 200**. Response:

```json
{
  "id": "<CASH_ID>",
  "name": "Cash",
  "type": "ASSET",
  "balance": "0.00"
}
```

Note: the response contains `id`, `name`, `type`, and `balance` only — no transactions array.

### 1.6 Get Account — Not Found (404)

```bash
response=$(curl -s -w "\n%{http_code}" \
  http://localhost:8000/api/accounts/00000000-0000-0000-0000-000000000000)
echo "$response" | sed \$d | jq .
echo "→ HTTP $(echo "$response" | tail -1)"
```

Expected: **HTTP 404**.

### 1.7 List All Accounts

```bash
curl -s http://localhost:8000/api/accounts | jq .
```

Expected: **HTTP 200**. Paginated envelope:

```json
{
  "items": [
    {"id": "...", "name": "Cash", "type": "ASSET", "balance": "0.00"},
    {"id": "...", "name": "Office Supplies", "type": "EXPENSE", "balance": "0.00"}
  ],
  "total": 2,
  "limit": null,
  "offset": 0
}
```

Both accounts from steps above should be present with `balance: "0.00"`.

---

## 2. Transaction Processing

These tests use `CASH_ID` and `SUPPLIES_ID` from [section 1](#1-account-management).

### 2.1 Create Transaction — Success

```bash
response=$(curl -s -w "\n%{http_code}" -X POST http://localhost:8000/api/transactions \
  -H "Content-Type: application/json" \
  -d "{
    \"description\": \"Buy supplies with cash\",
    \"date\": \"2026-03-01T10:00:00Z\",
    \"entries\": [
      {\"accountId\": \"$SUPPLIES_ID\", \"type\": \"DEBIT\", \"amount\": 100.00},
      {\"accountId\": \"$CASH_ID\", \"type\": \"CREDIT\", \"amount\": 100.00}
    ]
  }")
body=$(echo "$response" | sed \$d)
echo "$body" | jq .
echo "→ HTTP $(echo "$response" | tail -1)"
TXN_ID=$(echo "$body" | jq -r '.id')
echo "→ TXN_ID=$TXN_ID"
```

Expected: **HTTP 201**. Response contains `id`, `description`, `timestamp`, and `entries` array with 2 items.

After this transaction, verify balances updated:

```bash
curl -s "http://localhost:8000/api/accounts/$CASH_ID" | jq '{name, balance}'
```

Expected: `"balance": "-100.00"` — ASSET accounts: balance = debits - credits. Cash had 0 debits and 100 credits, so balance = -100.00. This is correct — cash decreased.

```bash
curl -s "http://localhost:8000/api/accounts/$SUPPLIES_ID" | jq '{name, balance}'
```

Expected: `"balance": "100.00"` — EXPENSE account: balance = debits - credits = 100 - 0 = 100.00.

### 2.2 Fewer Than 2 Entries (400)

```bash
response=$(curl -s -w "\n%{http_code}" -X POST http://localhost:8000/api/transactions \
  -H "Content-Type: application/json" \
  -d "{
    \"description\": \"Single entry\",
    \"date\": \"2026-03-01T10:00:00Z\",
    \"entries\": [
      {\"accountId\": \"$CASH_ID\", \"type\": \"DEBIT\", \"amount\": 50.00}
    ]
  }")
echo "$response" | sed \$d | jq .
echo "→ HTTP $(echo "$response" | tail -1)"
```

Expected: **HTTP 400**. Detail: "Transaction must have at least 2 entries".

### 2.3 All Same Type — No CREDIT (400)

```bash
response=$(curl -s -w "\n%{http_code}" -X POST http://localhost:8000/api/transactions \
  -H "Content-Type: application/json" \
  -d "{
    \"description\": \"All debits\",
    \"date\": \"2026-03-01T10:00:00Z\",
    \"entries\": [
      {\"accountId\": \"$CASH_ID\", \"type\": \"DEBIT\", \"amount\": 50.00},
      {\"accountId\": \"$SUPPLIES_ID\", \"type\": \"DEBIT\", \"amount\": 50.00}
    ]
  }")
echo "$response" | sed \$d | jq .
echo "→ HTTP $(echo "$response" | tail -1)"
```

Expected: **HTTP 400**. Detail: "Transaction must have at least one CREDIT entry".

### 2.4 Unbalanced Transaction (400)

```bash
response=$(curl -s -w "\n%{http_code}" -X POST http://localhost:8000/api/transactions \
  -H "Content-Type: application/json" \
  -d "{
    \"description\": \"Unbalanced\",
    \"date\": \"2026-03-01T10:00:00Z\",
    \"entries\": [
      {\"accountId\": \"$SUPPLIES_ID\", \"type\": \"DEBIT\", \"amount\": 100.00},
      {\"accountId\": \"$CASH_ID\", \"type\": \"CREDIT\", \"amount\": 50.00}
    ]
  }")
echo "$response" | sed \$d | jq .
echo "→ HTTP $(echo "$response" | tail -1)"
```

Expected: **HTTP 400**. Detail: "Total debits (100.00) must equal total credits (50.00)".

### 2.5 Non-Existent Account in Entry (404)

```bash
response=$(curl -s -w "\n%{http_code}" -X POST http://localhost:8000/api/transactions \
  -H "Content-Type: application/json" \
  -d "{
    \"description\": \"Ghost account\",
    \"date\": \"2026-03-01T10:00:00Z\",
    \"entries\": [
      {\"accountId\": \"00000000-0000-0000-0000-000000000000\", \"type\": \"DEBIT\", \"amount\": 100.00},
      {\"accountId\": \"$CASH_ID\", \"type\": \"CREDIT\", \"amount\": 100.00}
    ]
  }")
echo "$response" | sed \$d | jq .
echo "→ HTTP $(echo "$response" | tail -1)"
```

Expected: **HTTP 404**. Detail: "Account 00000000-0000-0000-0000-000000000000 not found".

### 2.6 Negative Amount (400)

```bash
response=$(curl -s -w "\n%{http_code}" -X POST http://localhost:8000/api/transactions \
  -H "Content-Type: application/json" \
  -d "{
    \"description\": \"Negative amount\",
    \"date\": \"2026-03-01T10:00:00Z\",
    \"entries\": [
      {\"accountId\": \"$SUPPLIES_ID\", \"type\": \"DEBIT\", \"amount\": -100.00},
      {\"accountId\": \"$CASH_ID\", \"type\": \"CREDIT\", \"amount\": -100.00}
    ]
  }")
echo "$response" | sed \$d | jq .
echo "→ HTTP $(echo "$response" | tail -1)"
```

Expected: **HTTP 400**. Detail: "All entry amounts must be positive".

### 2.7 Zero Amount (400)

```bash
response=$(curl -s -w "\n%{http_code}" -X POST http://localhost:8000/api/transactions \
  -H "Content-Type: application/json" \
  -d "{
    \"description\": \"Zero amount\",
    \"date\": \"2026-03-01T10:00:00Z\",
    \"entries\": [
      {\"accountId\": \"$SUPPLIES_ID\", \"type\": \"DEBIT\", \"amount\": 0},
      {\"accountId\": \"$CASH_ID\", \"type\": \"CREDIT\", \"amount\": 0}
    ]
  }")
echo "$response" | sed \$d | jq .
echo "→ HTTP $(echo "$response" | tail -1)"
```

Expected: **HTTP 400**. Detail: "All entry amounts must be positive".

### 2.8 Empty Description (400)

```bash
response=$(curl -s -w "\n%{http_code}" -X POST http://localhost:8000/api/transactions \
  -H "Content-Type: application/json" \
  -d "{
    \"description\": \"\",
    \"date\": \"2026-03-01T10:00:00Z\",
    \"entries\": [
      {\"accountId\": \"$SUPPLIES_ID\", \"type\": \"DEBIT\", \"amount\": 100.00},
      {\"accountId\": \"$CASH_ID\", \"type\": \"CREDIT\", \"amount\": 100.00}
    ]
  }")
echo "$response" | sed \$d | jq .
echo "→ HTTP $(echo "$response" | tail -1)"
```

Expected: **HTTP 400**. Detail: "Transaction description must not be empty".

### 2.9 Get Transaction by ID

Using `TXN_ID` from [step 2.1](#21-create-transaction--success):

```bash
curl -s "http://localhost:8000/api/transactions/$TXN_ID" | jq .
```

Expected: **HTTP 200**. Response:

```json
{
  "id": "<TXN_ID>",
  "description": "Buy supplies with cash",
  "timestamp": "2026-03-01T10:00:00+00:00",
  "entries": [
    {"id": "...", "accountId": "<SUPPLIES_ID>", "type": "DEBIT", "amount": "100.00"},
    {"id": "...", "accountId": "<CASH_ID>", "type": "CREDIT", "amount": "100.00"}
  ]
}
```

### 2.10 Get Transaction — Not Found (404)

```bash
response=$(curl -s -w "\n%{http_code}" \
  http://localhost:8000/api/transactions/00000000-0000-0000-0000-000000000000)
echo "$response" | sed \$d | jq .
echo "→ HTTP $(echo "$response" | tail -1)"
```

Expected: **HTTP 404**.

---

## 3. Transaction Listing and Filtering

### 3.1 List All Transactions

```bash
curl -s http://localhost:8000/api/transactions | jq .
```

Expected: **HTTP 200**. Paginated envelope with all transactions:

```json
{
  "items": [ ... ],
  "total": "<count>",
  "limit": null,
  "offset": 0
}
```

Verify total count:

```bash
curl -s http://localhost:8000/api/transactions | jq '.total'
```

### 3.2 Pagination

```bash
curl -s "http://localhost:8000/api/transactions?limit=1&offset=0" | jq .
```

Expected: **HTTP 200**. `items` has exactly 1 transaction, `total` is the full count, `limit` is 1, `offset` is 0.

```bash
curl -s "http://localhost:8000/api/transactions?limit=1&offset=1" | jq .
```

Expected: `items` has the *second* transaction (different from the first page).

### 3.3 Date Range Filter

Filter for transactions in March 2026 only (excludes the April interest payment in seeded data):

```bash
curl -s "http://localhost:8000/api/transactions?from_date=2026-03-01T00:00:00Z&to_date=2026-03-31T23:59:59Z" | jq .
```

Expected: **HTTP 200**. Only transactions with timestamps between Mar 1 and Mar 31 inclusive. If using seed data, this should return 6 transactions (all except the Apr 1 interest payment).

Verify the count:

```bash
curl -s "http://localhost:8000/api/transactions?from_date=2026-03-01T00:00:00Z&to_date=2026-03-31T23:59:59Z" | jq '.total'
```

### 3.4 Transactions for Account

Using `CASH_ID` from [step 1.1](#11-create-account--success):

```bash
curl -s "http://localhost:8000/api/accounts/$CASH_ID/transactions" | jq .
```

Expected: **HTTP 200**. Paginated envelope containing only transactions that have an entry affecting the Cash account.

Supports the same filters:

```bash
curl -s "http://localhost:8000/api/accounts/$CASH_ID/transactions?limit=2&offset=0" | jq .
```

Expected: at most 2 items in `items`.

### 3.5 Transactions for Non-Existent Account (404)

```bash
response=$(curl -s -w "\n%{http_code}" \
  "http://localhost:8000/api/accounts/00000000-0000-0000-0000-000000000000/transactions")
echo "$response" | sed \$d | jq .
echo "→ HTTP $(echo "$response" | tail -1)"
```

Expected: **HTTP 404**.

---

## 4. Balance Calculation (Double-Entry Rules)

This section uses the seed data to verify balances are computed dynamically from entries.

### 4.1 Seed Data and Verify Balances

Reset and seed the database:

```bash
make db-reset
make seed-data
```

The seed script creates 10 accounts and 7 transactions. Fetch all accounts:

```bash
curl -s http://localhost:8000/api/accounts | jq .
```

Expected balances (verify each one):

| Account | Type | Expected Balance | How Computed |
|---|---|---|---|
| Cash | ASSET | 700.00 | DR 1950 - CR 1250 = 700 |
| Office Supplies | EXPENSE | 600.00 | DR 600 - CR 0 = 600 |
| Accounts Payable | LIABILITY | 0.00 | CR 400 - DR 400 = 0 |
| Sales Revenue | REVENUE | 1000.00 | CR 1000 - DR 0 = 1000 |
| Accounts Receivable | ASSET | 0.00 | DR 1000 - CR 1000 = 0 |
| Inventory | ASSET | 0.00 | DR 600 - CR 600 = 0 |
| Cost of Goods Sold | EXPENSE | 600.00 | DR 600 - CR 0 = 600 |
| Bank Loan | LIABILITY | 1000.00 | CR 1000 - DR 0 = 1000 |
| Loan Fees | EXPENSE | 50.00 | DR 50 - CR 0 = 50 |
| Interest Expense | EXPENSE | 50.00 | DR 50 - CR 0 = 50 |

Verify a specific account (e.g. Cash):

```bash
CASH_ID=$(curl -s http://localhost:8000/api/accounts | jq -r '.items[] | select(.name == "Cash") | .id')
echo "→ CASH_ID=$CASH_ID"
curl -s "http://localhost:8000/api/accounts/$CASH_ID" | jq '{name, balance}'
```

Expected: `"balance": "700.00"`

### 4.2 Balance Rules by Account Type

The balance formula depends on account type:

| Account Type | Formula | Increase With | Decrease With |
|---|---|---|---|
| ASSET | debits - credits | DEBIT | CREDIT |
| EXPENSE | debits - credits | DEBIT | CREDIT |
| LIABILITY | credits - debits | CREDIT | DEBIT |
| REVENUE | credits - debits | CREDIT | DEBIT |

**Verify with a new transaction** — add $50 to Cash (ASSET) via debit, funded by Revenue (REVENUE) credit:

First, get account IDs from the seeded data:

```bash
CASH_ID=$(curl -s http://localhost:8000/api/accounts | jq -r '.items[] | select(.name == "Cash") | .id')
echo "→ CASH_ID=$CASH_ID"

REVENUE_ID=$(curl -s http://localhost:8000/api/accounts | jq -r '.items[] | select(.name == "Sales Revenue") | .id')
echo "→ REVENUE_ID=$REVENUE_ID"
```

Create the transaction:

```bash
response=$(curl -s -w "\n%{http_code}" -X POST http://localhost:8000/api/transactions \
  -H "Content-Type: application/json" \
  -d "{
    \"description\": \"Additional revenue collected\",
    \"date\": \"2026-04-02T10:00:00Z\",
    \"entries\": [
      {\"accountId\": \"$CASH_ID\", \"type\": \"DEBIT\", \"amount\": 50.00},
      {\"accountId\": \"$REVENUE_ID\", \"type\": \"CREDIT\", \"amount\": 50.00}
    ]
  }")
body=$(echo "$response" | sed \$d)
echo "$body" | jq .
echo "→ HTTP $(echo "$response" | tail -1)"
TXN_ID=$(echo "$body" | jq -r '.id')
echo "→ TXN_ID=$TXN_ID"
```

Expected: **HTTP 201**.

Now verify the balances shifted correctly:

```bash
curl -s "http://localhost:8000/api/accounts/$CASH_ID" | jq '{name, balance}'
```

Expected: Cash balance changed from `700.00` to `750.00` (ASSET increased by DEBIT).

```bash
curl -s "http://localhost:8000/api/accounts/$REVENUE_ID" | jq '{name, balance}'
```

Expected: Sales Revenue balance changed from `1000.00` to `1050.00` (REVENUE increased by CREDIT).

### 4.3 Accounting Equation Check

After the 7 seed transactions, the accounting equation must hold:

```
Assets = Liabilities + Equity
```

Fetch all accounts and verify:

```bash
curl -s http://localhost:8000/api/accounts | jq '
  def sum_type(t): [.items[] | select(.type == t) | .balance | tonumber] | add // 0;
  "Assets:      \(sum_type("ASSET"))",
  "Liabilities: \(sum_type("LIABILITY"))",
  "Revenue:     \(sum_type("REVENUE"))",
  "Expenses:    \(sum_type("EXPENSE"))",
  "Equity:      \(sum_type("REVENUE") - sum_type("EXPENSE"))",
  "Balanced:    \((sum_type("ASSET") - sum_type("LIABILITY") - sum_type("REVENUE") + sum_type("EXPENSE")) | fabs < 0.01)"
'
```

Expected (with seed data only, before step 4.2):

```
Assets:      700
Liabilities: 1000
Revenue:     1000
Expenses:    1300
Equity:      -300
Balanced:    true
```

---

## Related Documents

- [API Specification](./api-specification.md) — endpoint contracts, request/response schemas
- [Use Cases](./use-cases.md) — seed data scenarios with journal entries
- [Domain Model](./domain-model.md) — balance calculation rules, validation rules
- [Development Guide](./development-guide.md) — running tests, database migrations
