# ADR-001: Clean Architecture

## Table of Contents
- [Status](#status)
- [Context](#context)
- [Decision](#decision)
- [Consequences](#consequences)
- [Related Documents](#related-documents)

## Status

**Accepted** -- 2024-03-04

## Context

The assessment requires:
- Business logic must NOT live in the API layer
- Business logic must be testable without running FastAPI
- Clear separation between API, service, domain, and persistence layers
- Proper error handling with no 500 errors on endpoints

We need an architecture that enforces these boundaries and makes violations obvious.

### Options Considered

1. **Clean Architecture (layered, dependency inversion)** -- Domain at center, infrastructure at edges
2. **Simple MVC** -- Models, views (routes), controllers
3. **Hexagonal Architecture (ports & adapters)** -- Similar to clean arch, more formal port definitions

## Decision

We adopt **Clean Architecture** with 4 layers:

```
API → Application → Domain ← Infrastructure
```

- **Domain layer** has zero dependencies. Pure Python dataclasses, enums, and functions.
- **Application layer** defines repository interfaces (protocols). Orchestrates use cases.
- **Infrastructure layer** implements those interfaces with SQLAlchemy.
- **API layer** is thin. Validates HTTP input, calls services, maps exceptions to HTTP codes.

We chose this over simple MVC because:
- MVC doesn't enforce "business logic outside controllers" structurally
- MVC tends to accumulate logic in controllers over time
- Clean Architecture makes the domain testable by definition (no imports to mock)

We chose this over Hexagonal because:
- Hexagonal adds formality (explicit port interfaces for every interaction) that isn't needed at this project's scale
- Clean Architecture achieves the same testability goals with less boilerplate

## Consequences

### Positive

- **Testability**: Domain logic is tested with plain `pytest` -- no mocking, no fixtures, no DB
- **Enforced boundaries**: Import rules make it obvious when a layer is violated
- **Maintainability**: Changes to the DB schema don't touch business rules
- **Assessment alignment**: Directly satisfies "business logic must be testable without FastAPI"

### Negative

- **More files**: 4 layers means more directories and files than a flat structure
- **Mapping overhead**: Domain models ↔ ORM models ↔ Pydantic schemas requires mappers
- **Indirection**: A request traverses 4 layers, which can feel like overkill for simple CRUD

### Trade-offs Accepted

The mapping overhead is worth it for a financial system where correctness matters. The extra files are manageable at this project's size (3 entities, 6 endpoints).

## Related Documents

- [Architecture](../architecture.md) -- full layer diagram and responsibilities
- [Domain Model](../domain-model.md) -- what lives in the domain layer
