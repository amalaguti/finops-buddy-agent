# Development

## Spec-driven development

FinOps Buddy uses **spec-driven development**: behavior is described in structured specifications (requirements and scenarios) before and during implementation, then checked with automated tests. **OpenSpec** lives under **`openspec/`** — canonical capabilities in **`openspec/specs/`**, and each change as proposals, design notes, delta specs, and task checklists under **`openspec/changes/`** (completed work under **`openspec/changes/archive/`**).

## Day-to-day workflow

- **Install:** `poetry install` (creates venv and installs deps from lockfile; use `poetry install --no-root` to skip installing the package itself).
- **Run CLI:** `poetry run finops whoami` (or `poetry run python -m finops_buddy whoami`).
- **Build hosted frontend:** `cd frontend && npm run build:hosted` (writes hosted UI assets into `src/finops_buddy/webui/`). For a **full rebuild** (package or Docker image with latest UI), see [Running FinOps Buddy — Build flow](./RUNNING.md#build-flow-full-rebuild).
- **Lint/format:** `poetry run ruff check .` / `poetry run ruff format .`
- **Tests:** `poetry run pytest` (from repo root).
- **Pre-commit:** Run `pre-commit install` to run Ruff and Bandit on commit.

## Security scanning

- **Bandit** — Python security linter:
  ```bash
  poetry run bandit -c pyproject.toml -r src/
  ```
  Configuration in `pyproject.toml` under `[tool.bandit]`.

- **pip-audit** — Dependency vulnerability scanner:
  ```bash
  poetry run pip-audit
  ```
  Run before releases or when dependencies change. If a vulnerability has no fix, use `--ignore-vuln VULN-ID` and document it.
  **pygments** may report **CVE-2026-4539** while PyPI still lists 2.19.2 as latest; until a fixed release exists, use `poetry run pip-audit --ignore-vuln CVE-2026-4539` and track [Pygments releases](https://pypi.org/project/pygments/).

## CLI reference (after `poetry install`)

- `poetry run finops whoami` — show current AWS identity (account ID, principal ARN)
- `poetry run finops profiles` — list configured AWS profiles from `~/.aws/config`
- `poetry run finops context` — show current account and Master/Payer status (set `FINOPS_MASTER_PROFILE` or `FINOPS_MASTER_ACCOUNT_ID` to designate master)
- `poetry run finops verify` — verify AWS credentials for the current or `--profile` profile; optionally `--account-id ID` to require a specific account
- `poetry run finops costs` — show current-month costs by service in a table (requires Cost Explorer enabled)
- `poetry run finops chat` — start interactive chat with the FinOps agent (cost analysis; use `--profile NAME` for a specific AWS profile; use `--quiet` or `-q` to suppress startup progress messages)
- `poetry run finops serve` — start the HTTP API server (profiles, context, costs, chat); bind address and port from settings or `FINOPS_SERVER_HOST` / `FINOPS_SERVER_PORT` (default 127.0.0.1:8000). Use `--reload` to auto-restart on code changes.

Or activate the shell with `poetry shell`, then run `finops whoami`, `finops costs`, `finops chat`, etc.

### Chat reserved commands (in `finops chat`)

- `/quit` — exit the chat session
- `/tooling` — show available tools (built-in and MCP servers such as AWS Knowledge MCP Server and their tools); no LLM call
- `/status` — check MCP server readiness (e.g. after uvx is done installing); shows ready/not ready per server; no LLM call
- `/credentials` — show AWS credentials in use (profile, region, account, ARN); same as `finops verify`; these are passed to MCP servers; no LLM call
- `/context` — show conversation context (turns, profile, account, model, provider, token usage when available); no LLM call

More detail: [Configuration](./CONFIGURATION.md) (chat behavior, MCP flags).
