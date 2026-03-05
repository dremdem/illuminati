# Use Cases

Three multi-step business scenarios that demonstrate double-entry bookkeeping with the Financial Ledger API.

## Table of Contents

- [Overview](#overview)
- [Seeded Accounts](#seeded-accounts)
- [Scenario 1: Purchase Office Supplies](#scenario-1-purchase-office-supplies)
- [Scenario 2: Sell Goods on Credit](#scenario-2-sell-goods-on-credit)
- [Scenario 3: Borrow Money from a Bank](#scenario-3-borrow-money-from-a-bank)
- [Final Balances](#final-balances)
- [See Also](#see-also)

## Overview

The seed script (`make seed-data`) loads all three scenarios into a running instance. You can also replay them manually with `curl` using the JSON payloads below.

```bash
# Load all scenarios at once
make seed-data
```

Each scenario creates accounts and transactions that follow real-world accounting patterns. Every transaction balances (total debits = total credits), and the final balances satisfy the accounting equation:

> **Assets = Liabilities + Equity**

## Seeded Accounts

| Account | Type |
|---|---|
| Cash | ASSET |
| Office Supplies | EXPENSE |
| Accounts Payable | LIABILITY |
| Sales Revenue | REVENUE |
| Accounts Receivable | ASSET |
| Inventory | ASSET |
| Cost of Goods Sold | EXPENSE |
| Bank Loan | LIABILITY |
| Loan Fees | EXPENSE |
| Interest Expense | EXPENSE |

Create them via the API:

```bash
curl -X POST http://localhost:8000/api/accounts \
  -H "Content-Type: application/json" \
  -d '{"name": "Cash", "type": "ASSET"}'
```

Repeat for each account, changing the `name` and `type` values.

## Scenario 1: Purchase Office Supplies

A business buys $600 of office supplies, paying $200 cash and putting $400 on credit. Later, it pays the supplier.

### Transaction 1: Purchase supplies (Mar 1)

```bash
curl -X POST http://localhost:8000/api/transactions \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Purchase office supplies",
    "date": "2026-03-01T10:00:00Z",
    "entries": [
      {"accountId": "<office-supplies-id>", "type": "DEBIT", "amount": 600.00},
      {"accountId": "<cash-id>", "type": "CREDIT", "amount": 200.00},
      {"accountId": "<accounts-payable-id>", "type": "CREDIT", "amount": 400.00}
    ]
  }'
```

| Account | Debit | Credit |
|---|---|---|
| Office Supplies | $600 | |
| Cash | | $200 |
| Accounts Payable | | $400 |

### Transaction 2: Pay supplier (Mar 5)

```bash
curl -X POST http://localhost:8000/api/transactions \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Pay office supply supplier",
    "date": "2026-03-05T10:00:00Z",
    "entries": [
      {"accountId": "<accounts-payable-id>", "type": "DEBIT", "amount": 400.00},
      {"accountId": "<cash-id>", "type": "CREDIT", "amount": 400.00}
    ]
  }'
```

| Account | Debit | Credit |
|---|---|---|
| Accounts Payable | $400 | |
| Cash | | $400 |

**Result:** Office Supplies balance is $600. Accounts Payable is zeroed out. Cash decreased by $600 total.

## Scenario 2: Sell Goods on Credit

A business purchases inventory, sells it on credit at a markup, and later collects payment.

### Transaction 1: Purchase inventory (Mar 3)

```bash
curl -X POST http://localhost:8000/api/transactions \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Purchase inventory for resale",
    "date": "2026-03-03T10:00:00Z",
    "entries": [
      {"accountId": "<inventory-id>", "type": "DEBIT", "amount": 600.00},
      {"accountId": "<cash-id>", "type": "CREDIT", "amount": 600.00}
    ]
  }'
```

| Account | Debit | Credit |
|---|---|---|
| Inventory | $600 | |
| Cash | | $600 |

### Transaction 2: Sell goods on credit (Mar 10)

This compound transaction records both the revenue and the cost of goods sold:

```bash
curl -X POST http://localhost:8000/api/transactions \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Sale of goods on credit",
    "date": "2026-03-10T14:00:00Z",
    "entries": [
      {"accountId": "<accounts-receivable-id>", "type": "DEBIT", "amount": 1000.00},
      {"accountId": "<sales-revenue-id>", "type": "CREDIT", "amount": 1000.00},
      {"accountId": "<cogs-id>", "type": "DEBIT", "amount": 600.00},
      {"accountId": "<inventory-id>", "type": "CREDIT", "amount": 600.00}
    ]
  }'
```

| Account | Debit | Credit |
|---|---|---|
| Accounts Receivable | $1,000 | |
| Sales Revenue | | $1,000 |
| Cost of Goods Sold | $600 | |
| Inventory | | $600 |

### Transaction 3: Customer pays (Mar 15)

```bash
curl -X POST http://localhost:8000/api/transactions \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Customer payment for goods",
    "date": "2026-03-15T09:00:00Z",
    "entries": [
      {"accountId": "<cash-id>", "type": "DEBIT", "amount": 1000.00},
      {"accountId": "<accounts-receivable-id>", "type": "CREDIT", "amount": 1000.00}
    ]
  }'
```

| Account | Debit | Credit |
|---|---|---|
| Cash | $1,000 | |
| Accounts Receivable | | $1,000 |

**Result:** Revenue of $1,000 recorded, COGS of $600, Inventory zeroed out, Cash increased by $400 net, Accounts Receivable zeroed out.

## Scenario 3: Borrow Money from a Bank

A business takes a $1,000 loan with a $50 origination fee, then makes an interest payment.

### Transaction 1: Loan disbursement (Mar 20)

The bank deducts a $50 fee from the disbursement:

```bash
curl -X POST http://localhost:8000/api/transactions \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Bank loan received",
    "date": "2026-03-20T11:00:00Z",
    "entries": [
      {"accountId": "<cash-id>", "type": "DEBIT", "amount": 950.00},
      {"accountId": "<loan-fees-id>", "type": "DEBIT", "amount": 50.00},
      {"accountId": "<bank-loan-id>", "type": "CREDIT", "amount": 1000.00}
    ]
  }'
```

| Account | Debit | Credit |
|---|---|---|
| Cash | $950 | |
| Loan Fees | $50 | |
| Bank Loan | | $1,000 |

### Transaction 2: Interest payment (Apr 1)

```bash
curl -X POST http://localhost:8000/api/transactions \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Loan interest payment",
    "date": "2026-04-01T10:00:00Z",
    "entries": [
      {"accountId": "<interest-expense-id>", "type": "DEBIT", "amount": 50.00},
      {"accountId": "<cash-id>", "type": "CREDIT", "amount": 50.00}
    ]
  }'
```

| Account | Debit | Credit |
|---|---|---|
| Interest Expense | $50 | |
| Cash | | $50 |

**Result:** $1,000 liability recorded, $50 loan fee expensed, Cash increased by $900 net, $50 interest paid.

## Final Balances

After all 7 transactions, the ledger shows:

| Account | Type | Balance |
|---|---|---|
| Cash | ASSET | $700.00 |
| Office Supplies | EXPENSE | $600.00 |
| Accounts Payable | LIABILITY | $0.00 |
| Sales Revenue | REVENUE | $1,000.00 |
| Accounts Receivable | ASSET | $0.00 |
| Inventory | ASSET | $0.00 |
| Cost of Goods Sold | EXPENSE | $600.00 |
| Bank Loan | LIABILITY | $1,000.00 |
| Loan Fees | EXPENSE | $50.00 |
| Interest Expense | EXPENSE | $50.00 |

### Accounting Equation

```
Assets = Liabilities + Equity

Assets:
  Cash               $700.00
  Accounts Receivable   $0.00
  Inventory             $0.00
  ─────────────────────────────
  Total Assets        $700.00

Liabilities:
  Accounts Payable      $0.00
  Bank Loan         $1,000.00
  ─────────────────────────────
  Total Liabilities $1,000.00

Equity (Revenue − Expenses):
  Sales Revenue     $1,000.00
  Office Supplies    −$600.00
  Cost of Goods Sold −$600.00
  Loan Fees           −$50.00
  Interest Expense    −$50.00
  ─────────────────────────────
  Total Equity       −$300.00

$700 = $1,000 + (−$300) ✓
```

## See Also

- [Domain Model](./domain-model.md) -- entities, balance rules, and validation
- [API Specification](./api-specification.md) -- endpoint contracts and error codes
