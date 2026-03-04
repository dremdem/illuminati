# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## Critical Rules

### Git Workflow
- **NEVER push directly to master** - always use feature branches
- Create PR for all changes
- **ALWAYS check CI after pushing** - verify green checkmarks on PR page
- Wait for CI to pass before merging
- **One issue = one branch = one PR** — no exceptions
- Workflow: `issue → branch (feature/*) → TDD (tests first) → implement → PR → CI green → merge`

### Development Environment
- **All Python deps live inside Docker only** — no local venv required
- Use `docker compose run --rm app <command>` to run dev commands (lint, test, etc.)
- Use `Makefile` targets as shortcuts (`make lint`, `make test`, `make up`)

### TDD Approach
- **Always write tests first**, then implement to make them pass
- Unit tests: domain logic (no DB, no HTTP)
- Integration tests: repository layer (testcontainers + real PostgreSQL)
- API tests: full endpoint tests (httpx + TestClient)

## Style Guide

### Docstrings
- **Every function/method** must have a docstring with:
  - Description of what it does
  - `:param` for each parameter
  - `:return` for the return value
- **Every class** must have a description docstring
- Format: reStructuredText style (`:param`, `:return`)

Example:
```python
def validate_transaction_entries(
    entries: Sequence[TransactionEntry],
    description: str,
) -> None:
    """
    Validate transaction entries against double-entry bookkeeping rules.

    :param entries: list of debit/credit entries to validate
    :param description: human-readable transaction description
    :raises InvalidTransactionError: if entries violate structural rules
    :raises UnbalancedTransactionError: if total debits != total credits
    """
```

## Documentation Guidelines

When creating or updating documentation:

1. **Table of Contents**: Every document must have a TOC at the top with anchor links
2. **Mermaid Diagrams**: Use [Mermaid.js](https://mermaid.js.org/) for all diagrams (no ASCII art)
3. **Cross-References**: Link to related documents where applicable
4. **Code Examples**: Include runnable examples where possible
5. **Keep Updated**: Update docs when code changes
6. **Doc Navigator**: When adding or updating docs, always update [`docs/README.md`](docs/README.md) to reflect the change
