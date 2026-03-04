# ADR-002: Balance Computation Strategy

## Table of Contents
- [Status](#status)
- [Context](#context)
- [Decision](#decision)
- [Implementation](#implementation)
- [Consequences](#consequences)
- [Related Documents](#related-documents)

## Status

**Accepted** -- 2026-03-04

## Context

Account balances must be computed dynamically from transaction entries (never stored as a mutable column). The assessment allows two approaches:

1. **Python computation** -- Load all entries for an account, sum in Python
2. **SQL aggregation** -- Compute via `SUM(CASE WHEN ...)` in a database query

Balance calculation depends on account type:
- ASSET and EXPENSE: `sum(debits) - sum(credits)`
- LIABILITY and REVENUE: `sum(credits) - sum(debits)`

### Key Considerations

- An account could have thousands of entries in a real system
- `GET /api/accounts` must return balances for all accounts (N+1 risk)
- The balance formula involves conditional logic (account type determines sign)

## Decision

We use **SQL aggregation** for balance computation at the repository layer, with the balance **formula logic defined in the domain layer** for testability.

### Why Not Pure Python?

| Concern | Python | SQL |
|---|---|---|
| Memory | Loads all entries into memory | Constant memory |
| Performance | O(n) per account, N+1 for list | Single query for all accounts |
| Network | Transfers all entry rows | Transfers one number |
| Testability | Easy to unit test | Requires integration test |

### Hybrid Approach

- **Domain layer** defines the balance calculation rules (which types are debit-normal vs credit-normal) and has pure Python functions used in unit tests
- **Repository layer** implements the same logic as SQL aggregation for production use
- Unit tests verify the rules; integration tests verify the SQL produces the same results

## Implementation

The SQL query pattern:

```sql
SELECT
    a.id,
    a.name,
    a.type,
    COALESCE(
        CASE
            WHEN a.type IN ('ASSET', 'EXPENSE')
            THEN SUM(CASE WHEN te.type = 'DEBIT' THEN te.amount ELSE 0 END)
               - SUM(CASE WHEN te.type = 'CREDIT' THEN te.amount ELSE 0 END)
            ELSE
                 SUM(CASE WHEN te.type = 'CREDIT' THEN te.amount ELSE 0 END)
               - SUM(CASE WHEN te.type = 'DEBIT' THEN te.amount ELSE 0 END)
        END,
        0
    ) AS balance
FROM accounts a
LEFT JOIN transaction_entries te ON te.account_id = a.id
GROUP BY a.id, a.name, a.type;
```

The `LEFT JOIN` ensures accounts with no entries return a balance of `0`. The `COALESCE` handles NULL from empty aggregations.

## Consequences

### Positive

- **Performance**: Single query computes all balances, no N+1 problem
- **Scalability**: Works with any number of entries per account
- **Consistency**: Balance is always fresh (no stale cached values)
- **Testability preserved**: Domain layer still has pure Python balance logic for unit tests

### Negative

- **Dual implementation**: Balance logic exists in both Python (domain) and SQL (repository), must stay in sync
- **SQL complexity**: The CASE WHEN query is harder to read than Python
- **Testing**: The SQL path requires integration tests with a real database

### Mitigation

Integration tests explicitly verify that the SQL computation matches the domain layer's Python computation for all 4 account types.

## Related Documents

- [Domain Model: Balance Calculation](../domain-model.md#balance-calculation) -- rules table
- [Architecture](../architecture.md) -- where computation lives in each layer
