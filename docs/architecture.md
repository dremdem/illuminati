# Architecture

## Table of Contents
- [Overview](#overview)
- [Architectural Style](#architectural-style)
- [Layer Diagram](#layer-diagram)
- [Layer Responsibilities](#layer-responsibilities)
- [Dependency Rules](#dependency-rules)
- [Directory Mapping](#directory-mapping)
- [Request Flow](#request-flow)
- [Error Handling Strategy](#error-handling-strategy)
- [Related Documents](#related-documents)

## Overview

The Financial Ledger API follows **Clean Architecture** principles to separate business logic from infrastructure concerns. The primary goal is testability -- domain logic can be verified without a running database or HTTP server.

See [ADR-001: Clean Architecture](./adr/001-clean-architecture.md) for the decision rationale.

## Architectural Style

We use a **layered architecture** with strict dependency direction: outer layers depend on inner layers, never the reverse.

```
Outer (infrastructure) → Inner (domain)
```

The domain layer is the core of the application. It knows nothing about databases, HTTP, or frameworks.

## Layer Diagram

```mermaid
graph TB
    API["API Layer"]
    APP["Application Layer"]
    DOMAIN["Domain Layer"]
    INFRA["Infrastructure Layer"]

    API -->|"HTTP to Service call"| APP
    APP -->|"uses business rules"| DOMAIN
    APP -->|"calls via interface"| INFRA
    INFRA -->|"maps to/from"| DOMAIN

    style DOMAIN fill:#ee5a24,color:#fff
    style APP fill:#ff9f43,color:#fff
    style API fill:#4a9eff,color:#fff
    style INFRA fill:#7d5fff,color:#fff
```

| Layer | Contains |
|---|---|
| **API** (blue) | FastAPI Routers, Pydantic Schemas |
| **Application** (orange) | Services, Use Cases |
| **Domain** (red) | Entities, Business Rules, Exceptions |
| **Infrastructure** (purple) | SQLAlchemy Models, Repositories, DB |

## Layer Responsibilities

### Domain Layer (`src/ledger/domain/`)

The innermost layer. Pure Python with **zero external dependencies**.

| Module | Purpose |
|---|---|
| `models.py` | `Account`, `Transaction`, `TransactionEntry` dataclasses |
| `enums.py` | `AccountType` (ASSET, LIABILITY, REVENUE, EXPENSE), `EntryType` (DEBIT, CREDIT) |
| `services.py` | `validate_transaction()`, `calculate_balance()` |
| `exceptions.py` | `DomainError` base, `InvalidTransactionError`, `UnbalancedTransactionError`, `AccountNotFoundError`, `TransactionNotFoundError`, `DuplicateAccountError` |

**Rules:**
- No imports from `application`, `infrastructure`, or `api`
- No SQLAlchemy, no FastAPI, no Pydantic (for ORM/HTTP concerns)
- Uses `Decimal` for all monetary values (never `float`)
- Must be testable with plain `pytest` -- no fixtures, no DB, no HTTP

### Application Layer (`src/ledger/application/`)

Orchestrates use cases by combining domain logic with repository calls.

| Module | Purpose |
|---|---|
| `interfaces.py` | Repository protocols (`AccountRepository`, `TransactionRepository`) using `typing.Protocol`. `AccountRepository` includes `get_with_balance()` and `get_all_with_balances()` for SQL-aggregated balance retrieval. |
| `pagination.py` | `PaginatedResult[T]` frozen dataclass -- generic paginated container (items + total count). Used by services to return paginated data. |
| `account_service.py` | `AccountService`: create account, get account with balance, list accounts. Returns `AccountWithBalance` DTO (or `PaginatedResult[AccountWithBalance]` for lists). Depends only on `AccountRepository` (balance is computed at the repository layer via SQL aggregation). |
| `transaction_service.py` | `TransactionService`: create transaction (validate accounts + entries, persist), get by ID, get by account, list all. Uses `EntryData` DTO, returns `PaginatedResult` for list operations. |

**Rules:**
- Depends on `domain` (uses entities and business rules)
- Depends on repository **interfaces** (not implementations)
- No direct DB access, no SQL, no SQLAlchemy imports
- No HTTP concerns (no FastAPI, no status codes)

### Infrastructure Layer (`src/ledger/infrastructure/`)

Implements persistence and external integrations.

| Module | Purpose |
|---|---|
| `database.py` | Async SQLAlchemy engine, session factory, `get_db()` |
| `models.py` | SQLAlchemy ORM models (`AccountModel`, `TransactionModel`, `TransactionEntryModel`) |
| `mappers.py` | Domain↔ORM conversion functions (handles `type`↔`account_type`/`entry_type` mapping) |
| `repositories/account_repo.py` | `SqlaAccountRepository` -- implements `AccountRepository` protocol |
| `repositories/transaction_repo.py` | `SqlaTransactionRepository` -- implements `TransactionRepository` protocol |

**Rules:**
- Implements interfaces defined in `application`
- Maps between domain models and ORM models
- All DB-specific logic lives here (queries, transactions, constraints)
- Depends on `domain` for entity types

### API Layer (`src/ledger/api/`)

Thin HTTP interface. No business logic.

| Module | Purpose |
|---|---|
| `routers/accounts.py` | Account endpoints: `POST /api/accounts`, `GET /api/accounts`, `GET /api/accounts/{id}` |
| `routers/transactions.py` | Transaction endpoints: `POST /api/transactions`, `GET /api/transactions`, `GET /api/transactions/{id}`, `GET /api/accounts/{id}/transactions` |
| `schemas.py` | Pydantic v2 request/response models for accounts and transactions (with camelCase aliases), paginated envelope schemas (`PaginatedAccountResponse`, `PaginatedTransactionResponse`) |
| `dependencies.py` | FastAPI DI chain: `get_session` → repos → `get_account_service` / `get_transaction_service` |
| `exception_handlers.py` | Maps domain exceptions to HTTP status codes (404, 409, 400) |

**Rules:**
- Route handlers are thin -- validate input, call service, return response
- No business logic (no balance calculations, no transaction validation)
- Maps domain exceptions to HTTP responses (400, 404, 409)
- Uses Pydantic schemas for request validation and response serialization

## Dependency Rules

```mermaid
graph LR
    API --> APP
    APP --> DOMAIN
    INFRA --> DOMAIN
    APP -.->|"interface only"| INFRA

    style DOMAIN fill:#ee5a24,color:#fff
    style APP fill:#ff9f43,color:#fff
    style API fill:#4a9eff,color:#fff
    style INFRA fill:#7d5fff,color:#fff
```

| Rule | Description |
|---|---|
| Domain imports nothing | Zero dependencies on other layers |
| Application imports domain | Uses entities, services, exceptions |
| Application defines interfaces | Repository protocols live in application layer |
| Infrastructure imports domain | Maps ORM models to/from domain entities |
| Infrastructure implements interfaces | Concrete repositories fulfill application protocols |
| API imports application | Calls services, never domain directly for mutations |
| **Never:** inner → outer | Domain never imports infrastructure or API |

## Directory Mapping

```
src/ledger/
├── domain/                     # INNER - Pure business logic
│   ├── __init__.py
│   ├── models.py               # Account, Transaction, TransactionEntry
│   ├── enums.py                # AccountType, EntryType
│   ├── services.py             # validate_transaction(), calculate_balance()
│   └── exceptions.py           # Domain-specific errors
├── application/                # MIDDLE - Use cases
│   ├── __init__.py
│   ├── interfaces.py           # Repository protocols (typing.Protocol)
│   ├── pagination.py           # PaginatedResult[T] generic container
│   ├── account_service.py      # Account use cases
│   └── transaction_service.py  # Transaction use cases
├── infrastructure/             # OUTER - DB, ORM
│   ├── __init__.py
│   ├── database.py             # Engine, session, get_db()
│   ├── models.py               # SQLAlchemy ORM models
│   ├── mappers.py              # Domain ↔ ORM mappers
│   └── repositories/
│       ├── __init__.py          # Re-exports SqlaAccountRepository, SqlaTransactionRepository
│       ├── account_repo.py     # SqlaAccountRepository
│       └── transaction_repo.py # SqlaTransactionRepository
├── api/                        # OUTER - HTTP
│   ├── __init__.py
│   ├── schemas.py              # Pydantic request/response models
│   ├── dependencies.py         # DI wiring
│   ├── exception_handlers.py   # Domain exception → HTTP response
│   └── routers/
│       ├── __init__.py
│       ├── accounts.py         # /api/accounts
│       └── transactions.py     # /api/transactions
└── main.py                     # App factory with async lifespan (DB engine/session), CORS middleware
```

## Request Flow

Example: `POST /api/transactions` (creating a balanced transaction)

```mermaid
sequenceDiagram
    participant C as Client
    participant R as Router
    participant S as Service
    participant D as Domain
    participant Repo as Repository
    participant DB as PostgreSQL

    C->>R: POST /api/transactions
    R->>R: Validate request (Pydantic)
    R->>S: create_transaction(data)
    S->>D: validate_transaction(entries)
    D-->>S: OK or raise InvalidTransactionError
    S->>Repo: create(transaction)
    Repo->>DB: INSERT transaction + entries
    DB-->>Repo: OK
    Repo-->>S: Transaction (domain model)
    S-->>R: Transaction
    R-->>C: 201 Created (JSON)
```

## Error Handling Strategy

Domain exceptions are raised in the domain/application layers and translated to HTTP responses in the API layer:

| Domain Exception | HTTP Status | When |
|---|---|---|
| `UnbalancedTransactionError` | 400 Bad Request | sum(debits) != sum(credits) |
| `InvalidTransactionError` | 400 Bad Request | < 2 entries, missing debit/credit, negative amount |
| `AccountNotFoundError` | 404 Not Found | Referenced account doesn't exist |
| `TransactionNotFoundError` | 404 Not Found | Referenced transaction doesn't exist |
| `DuplicateAccountError` | 409 Conflict | Account name already taken |
| `DomainError` (base) | 400 Bad Request | Catch-all for business rule violations (e.g., empty account name) |
| `ValidationError` (Pydantic) | 422 Unprocessable Entity | Malformed request body |

## Related Documents

- [Domain Model](./domain-model.md) -- entity details, balance rules, validation
- [API Specification](./api-specification.md) -- endpoint contracts
- [Project Setup](./project-setup.md) -- tooling, Docker, CI
- [Development Guide](./development-guide.md) -- workflow, branching, testing
- [ADR-001: Clean Architecture](./adr/001-clean-architecture.md)
