# ADR-003: uv Over Poetry for Dependency Management

## Table of Contents
- [Status](#status)
- [Context](#context)
- [Decision](#decision)
- [Consequences](#consequences)
- [Related Documents](#related-documents)

## Status

**Accepted** -- 2024-03-04

## Context

The assessment suggests Poetry or pip-tools for dependency management. We need a tool that:

- Manages dependencies and lock files
- Works well inside Docker
- Integrates with `pyproject.toml` (PEP 621)
- Is fast and reliable in CI

### Options Considered

| Tool | Lock file | Speed | Docker integration | Standards compliance |
|---|---|---|---|---|
| **Poetry** | `poetry.lock` | Moderate | Needs installer or plugin | Uses `[tool.poetry]` (non-standard) |
| **pip-tools** | `requirements.txt` | Fast | Native pip | Manual `pyproject.toml` setup |
| **uv** | `uv.lock` | Very fast | Single binary, COPY-friendly | PEP 621 native |

## Decision

We use **uv** for dependency management.

### Rationale

1. **Speed**: uv resolves and installs dependencies 10-100x faster than Poetry. This directly improves Docker build times and CI duration.

2. **Docker-friendly**: uv is a single static binary. In a Dockerfile:
   ```dockerfile
   COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/
   ```
   No need for pip, no need for a Poetry installer, no virtualenv activation scripts.

3. **Standards-based**: uv uses standard `pyproject.toml` (`[project]` table, PEP 621) rather than Poetry's proprietary `[tool.poetry]` section. This makes the project compatible with any PEP 621-compliant tool.

4. **Lock file**: `uv.lock` provides reproducible builds (committed to repo). `uv sync --frozen` in Docker ensures exact versions.

5. **CI integration**: Official GitHub Action (`astral-sh/setup-uv@v5`) provides one-line setup.

## Consequences

### Positive

- **CI runs ~30s total** across 3 jobs (lint 9s, typecheck 12s, test 33s) -- uv's speed contributes to this
- **Dockerfile is simple** -- no multi-step Poetry installation
- **Standard pyproject.toml** -- no vendor lock-in
- **Dependency groups** -- dev dependencies separated via `[dependency-groups]`

### Negative

- **Less established** than Poetry in the Python ecosystem (uv is newer)
- **Assessment mentions Poetry** -- using uv is a deviation, though the assessment also says "or pip-tools" indicating flexibility
- **Team familiarity** -- developers familiar with Poetry may need to learn uv commands

### Migration Path

If uv needs to be replaced, the `pyproject.toml` is standard PEP 621 and works with Poetry (after adding `[tool.poetry]` metadata) or pip-tools (via `pip-compile`).

## Related Documents

- [Project Setup](../project-setup.md) -- how uv is used in the project
