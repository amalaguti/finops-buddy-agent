# Design: Foundation and AWS Identity

## Context

The aws_finops_agent project is CLI-first, Python-based, and will later add a backend and React frontend. This change establishes Phase 0 (repo hygiene and tooling) and minimal AWS identity resolution so that subsequent changes (e.g. cost visibility) can assume a known account context. No Strands agent or MCP integration in this change; credentials come from the existing AWS CLI config (profiles, env, or default).

## Goals / Non-Goals

**Goals:**
- Repo ready for spec-driven development: pre-commit, Ruff, pytest, clear package layout.
- Resolve “which AWS account/identity am I using?” using existing AWS config.
- List configured profiles/accounts/roles and support a simple notion of “current” or “Master/Payer” (config or placeholder).
- Provide a thin CLI entrypoint that can report identity and optionally list/select account.

**Non-Goals:**
- Full AWS Organizations integration or automatic Master/Payer discovery.
- Strands agent, MCP servers, or cost/anomaly features (those are Change 2).
- Backend API or frontend.

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Build / packaging** | Poetry | Dependency management, lockfile, single `pyproject.toml`; install with `poetry install`, run with `poetry run`. |
| **Linter** | Ruff | Fast, modern, replaces flake8/isort; good for Python 3.x. |
| **Test runner** | pytest | Standard for Python; supports fixtures and plugins. |
| **Config** | `pyproject.toml` for tool config | Poetry manages project metadata and deps; same file for Ruff, pytest. PROJECT_CONTEXT allows JSON + env for app config. |
| **Package layout** | Flat or `src/` layout under a package name (e.g. `finops_agent` or `aws_finops_agent`) | Keeps imports clear and allows `python -m` entrypoint. Prefer minimal layout for MVP (e.g. one package dir + `cli.py` or `__main__.py`). |
| **AWS identity source** | boto3 session + STS GetCallerIdentity + (optional) shared config file parsing | No new credential types; reuse default chain (env, profile, instance role). List profiles from `~/.aws/config` (or AWS_CONFIG_FILE) for “list accounts/roles.” |
| **Master/Payer** | Config-driven or placeholder | Config key (e.g. `master_account_id` or profile name) or env var; no Organizations API in this change. “Which account” = STS GetCallerIdentity; “is master?” = config lookup or default to “unknown.” |

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Profile listing differs by platform (paths, SSO) | Use boto3/session and standard AWS config paths; document SSO vs static credentials. |
| Over-scoping Phase 0 | Limit to: pre-commit (Ruff + optional pytest), pytest with one placeholder test, pyproject.toml. No CI YAML in this change unless trivial. |
| Master/Payer meaning unclear | Design treats it as “configured default” or “current account”; full org semantics deferred. |

## Migration Plan

- Add pre-commit config and hooks; developers run `pre-commit install`.
- Add `pyproject.toml` (or extend) with Ruff and pytest; existing code (if any) passes lint.
- Introduce package and CLI; no breaking change to external users (no prior release).
- No rollback beyond reverting commits; no data migration.

## Open Questions

- Exact CLI command names (e.g. `finops whoami`, `finops accounts list`) to be decided in tasks or follow-up.
- Whether to ship a minimal `config.json` / `.env.example` in this change or defer to when cost features need it.
