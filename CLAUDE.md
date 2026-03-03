# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## Critical Rules

### Git Workflow
- **NEVER push directly to master** - always use feature branches
- Create PR for all changes
- **ALWAYS check CI after pushing** - verify green checkmarks on PR page
- Wait for CI to pass before merging

## Documentation Guidelines

When creating or updating documentation:

1. **Table of Contents**: Every document must have a TOC at the top with anchor links
2. **Mermaid Diagrams**: Use [Mermaid.js](https://mermaid.js.org/) for all diagrams (no ASCII art)
3. **Cross-References**: Link to related documents where applicable
4. **Code Examples**: Include runnable examples where possible
5. **Keep Updated**: Update docs when code changes
