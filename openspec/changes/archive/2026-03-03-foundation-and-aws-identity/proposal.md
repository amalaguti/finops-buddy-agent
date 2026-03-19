# Proposal: Foundation and AWS Identity

## Why

The project needs a solid base for spec-driven development and a clear way to resolve which AWS account(s) the CLI operates against. Without repo tooling (lint, test, pre-commit), quality and consistency suffer; without AWS identity resolution, no cost or anomaly features can target the right account. This change establishes Phase 0 and the minimal identity/Master-Payer context required before building cost visibility (Change 2).

## What Changes

- **Phase 0 — Repo & tooling**: Add or verify pre-commit, Python linters (e.g. Ruff), pytest, and a project layout that supports CLI and future backend. No application code beyond scaffolding if needed.
- **AWS identity**: Use existing AWS CLI config; list configured profiles/accounts/roles; support filtering or configuration for “Master/Payer” (or a single account for now).
- **Master/Payer context**: Minimal capability to answer “which account am I using?” and to distinguish master/payer from linked accounts (placeholder or config-driven; no full org integration yet).
- **CLI entrypoint**: A thin CLI (e.g. `python -m` or a single entry script) that can report current identity and optionally list or select account.

## Capabilities

### New Capabilities

- `repo-tooling`: Pre-commit, linters (Ruff), pytest, project layout, and conventions so the repo is ready for spec-driven development.
- `aws-identity`: Resolve and list AWS identity (profiles, accounts, roles) using existing AWS CLI config; support configurable or default account selection.
- `master-payer-context`: Minimal Master/Payer context—identify current account and whether it is master/payer or linked (config or placeholder); no full org API required.

### Modified Capabilities

- None (no existing specs yet).

## Impact

- **Codebase**: New or updated config for pre-commit, Ruff, pytest; new Python package layout (e.g. `src/` or package root); optional `pyproject.toml` or `setup.cfg`.
- **Dependencies**: Pre-commit, Ruff, pytest, boto3 (and optionally AWS CLI config parsing). No Strands or MCP in this change.
- **Developers**: Must run pre-commit and tests before merging; branch-per-task remains the workflow (per config rules).
