# Documentation

## Table of Contents
- [Architecture & Design](#architecture--design)
- [API & Domain](#api--domain)
- [Development](#development)
- [Architecture Decision Records](#architecture-decision-records)

## Architecture & Design

| Document | Description |
|---|---|
| [Architecture](./architecture.md) | Clean architecture layers, dependency rules, request flow sequence diagram, error handling strategy |
| [Project Setup](./project-setup.md) | Tech stack, project structure, Docker setup, CI pipeline, Makefile targets, configuration files |

## API & Domain

| Document | Description |
|---|---|
| [Domain Model](./domain-model.md) | Entities (Account, Transaction, TransactionEntry), balance calculation rules, validation rules, worked examples |
| [API Specification](./api-specification.md) | All 6 REST endpoints with request/response contracts, status codes, curl examples, error matrix |

## Development

| Document | Description |
|---|---|
| [Development Guide](./development-guide.md) | Git workflow (one issue = one branch = one PR), TDD process, running tests, database migrations, code quality commands |

## Architecture Decision Records

| ADR | Decision | Status |
|---|---|---|
| [001 -- Clean Architecture](./adr/001-clean-architecture.md) | 4-layer clean architecture over MVC or hexagonal -- testability and boundary enforcement | Accepted |
| [002 -- Balance Computation](./adr/002-balance-computation.md) | SQL aggregation over Python computation -- performance, no N+1, constant memory | Accepted |
| [003 -- uv Over Poetry](./adr/003-uv-over-poetry.md) | uv for dependency management -- speed, Docker-friendly, PEP 621 native | Accepted |
