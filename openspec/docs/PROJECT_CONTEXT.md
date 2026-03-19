# AWS FinOps Agent — Project Context for OpenSpec

> **Purpose**: This document gives OpenSpec (and contributors) an initial picture of goals, design, requirements, planning, and constraints for the **aws_finops_agent** project. This document servers as a starting point, review and extend it before starting implementation.

**Optional: feed this into OpenSpec**  
To have OpenSpec (and the AI) use this when creating artifacts, add a short pointer in `openspec/config.yaml` under `context`, for example:

```yaml
context: |
  See openspec/docs/PROJECT_CONTEXT.md for goals, requirements, design, and constraints.
  Tech: Python CLI/backend, Strands Agents, React later. MVP = CLI only; read-only AWS.
```

---

## 1. Project Overview

| Item | Description |
|------|-------------|
| **Project name** | `aws_finops_agent` |
| **Type** | AI-powered FinOps assistant (CLI first, backend + frontend later) for AWS|
| **AI framework** | [Strands Agents](https://strandsagents.com/latest/) (AWS-native, multi-agent, model-agnostic), [AWS MCP servers support](https://awslabs.github.io/mcp/) |
| **Primary language** | Python (CLI and future backend) |
| **Future frontend** | React (candidate; Tailwind considered) |

**Vision**: A spec-driven project, AI-powered tool that helps with AWS cost visibility, anomalies, and analysis—starting as a pure CLI, designed so a backend API and web UI can be added later without redoing core logic.It must help user to visualize costs and be able to detect trends, compare month over month, week over week, biweekly over biweekly. It must produce historical analysis and when possible for top services be able to get information at the resource level (available for the last 14 days in AWS Cost Explorer)

---

## 2. Goals

- **OpenSpec-driven**: Use OpenSpec (or Spec Kit) and a spec workflow (e.g. [spec-workflow-mcp](https://github.com/Pimzino/spec-workflow-mcp)) so that **Requirements → Design → Tasks** are explicit and traceable.
- **Collaborative**: Encourage discussion and feedback at each stage (requirements, design, tasks).
- **Phased delivery**: Deliver an **MVP** first; once approved, move toward a **complete product**.
- **CLI-first**: Ship a **pure CLI module** first; backend and frontend work comes later.
- **Architecture-ready**: Design and code so that a Python backend and a React frontend can plug in later (shared core, clear boundaries).
- **MCP Support**: Use the following MCP servers as needed (see [mcp-servers-overlap-and-decisions.md](mcp-servers-overlap-and-decisions.md) for overlap analysis and rationale):
  - `aws-knowledge-mcp`
  - `awslabs.aws-documentation-mcp-server`
  - `awslabs.billing-cost-management-mcp-server` (covers Cost Explorer; we do **not** add the standalone cost-explorer MCP server)
  - `awslabs.aws-pricing-mcp-server` (implemented for bulk pricing, project scan, architecture patterns)
  - `awslabs.aws-diagram-mcp-server`

  All of these MCP servers are available at [awslabs.github.io/mcp](https://awslabs.github.io/mcp/).

---

## 3. Requirements

### 3.1 Spec & Documentation

- Keep requirements, design, and tasks aligned and referenced in OpenSpec artifacts.

### 3.2 MVP Scope (CLI-only)

| # | Requirement | Notes |
|---|-------------|--------|
| 1 | **Repo & tooling** | OpenSpec in place, **Poetry** for build and packaging, pre-commit, linters, pytest. Repo ready for spec-driven development. |
| 2 | **AWS identity** | Use existing AWS CLI config. List configured accounts/roles; filter for "Master/Payer account" (or configurable org). Use local credentials and assume roles per account as needed. |
| 3 | **Master/Payer account** | Ability to "connect" to Master/Payer account (exact integration TBD; placeholder for org/account context). and distinguish master/payer from linked accounts|
| 4 | **Costs this month** | Show current-month costs **per service** (e.g. Cost Explorer–style). |
| 5 | **Cost anomalies** | Show existing cost anomalies (e.g. Cost Anomaly Detection). |
| 6 | **CLI output** | Present costs and cost anomalies in **readable table format** in the CLI. |
| 7 | **Analysis** | Provide basic cost/anomaly **analysis** (exact capabilities to be refined in design). |
| 8 | **Marketplace costs** | Show **AWS Marketplace** costs. |
| 9 | **Saving plans** | Show **Saving Plans** costs, current savings and coverage, suggest new savings plans purchases. |
| 10 | **Reserved Instances** | Show **Reserved Instances** information, coverage. |
| 11 | **Costs Optimizations** | Identify possbile cost optimizations in the accounts. |


### 3.3 Post-MVP / Later

- **Backend**: Python API (same core logic as CLI).
- **Frontend**: Web UI (e.g. React + Tailwind); list accounts, initial cost summary.
- **Deep analysis**: Athena-based analysis (see AWS FinOps PRD reference).
- **Caching**: Caching layer for cost data per account; TTL e.g. 24 hours.

---

## 4. Design & Architecture

### 4.1 High-Level Design

- **CLI**: Entrypoint for all MVP features (accounts, costs, anomalies, tables, analysis).
- **Core**: Reusable Python modules (AWS clients, data shaping, formatting) so backend and CLI can share code.
- **Agent**: Strands-based agent for natural language or guided flows (e.g. "explain this spike," "which service grew most?"). Agent uses **read-only** AWS operations by default.
- **Future**: Backend = HTTP API around same core; frontend = React app calling backend.

### 4.2 Technical Choices

| Area | Choice | Rationale |
|------|--------|-----------|
| **Build / packaging** | **Poetry** | Dependency management, lockfile for reproducible installs, single `pyproject.toml` for metadata and tool config. |
| AI / agent | Strands Agents | AWS-native, multi-agent, Bedrock-friendly; good fit for FinOps tooling. |
| Config | JSON files + env vars | Config and env via JSON and `.env` (e.g. Python `dotenv` for `.env.local`). |
| Data (future) | SQLite + SQLAlchemy + Alembic | Local persistence and migrations when needed. |
| MCP | External or local (Docker) | Use settings to decide between external MCP or local Docker. |

### 4.3 Architectural Discussion

- Design and architecture should be discussed and agreed before implementation.  
- Reference: [architectural discussion thread](https://chatgpt.com/share/69a46207-fd34-8000-b76a-9941aa068a91) (for context only; decisions to be captured here or in OpenSpec).

---

## 5. Planning

### 5.1 Phases

1. **Phase 0 — Foundation**  
   OpenSpec workflow, repo hygiene (pre-commit, linters, pytest), project context (this doc).

2. **Phase 1 — MVP (CLI)**  
   Pure CLI: AWS identity + Master/Payer account context, current-month costs by service, cost anomalies, table output, basic analysis. Agent (Strands) integrated for assistant-style interaction.

3. **Phase 2 — Complete product (later)**  
   Backend API, optional DB (SQLite + Alembic), caching, deep analysis (e.g. Athena), then frontend (React).

### 5.2 Workflow Conventions

- Use **plan mode** where helpful; start new conversations per feature to keep context focused.
- Use **summarize** (or similar) to keep token usage under control.
- Prefer **Cursor commands** (e.g. `./cursor/commands/code-review.md`, `pr.md`) for review and PR checks.
- **Branches**: Review changes on branch (think through impact, lint, run tests, update docs).

---

## 6. Constraints & Guardrails

### 6.1 Safety & Operations

- **Read-only by default**: AWS operations used by the agent are read-only (no resource creation/deletion from the agent unless explicitly designed otherwise).
- **Credentials**: Use local credentials and assume roles as needed; no hardcoded secrets.

### 6.2 Code Quality

- **Pre-commit** hooks and **Python linters** to enforce good practices.
- **Pydantic** for data validation and settings.
- **Documented** functions and **modular** layout (child modules).
- **Pytest** for unit tests; **coverage ≥ 80%**.
- **Changelog**: Keep `CHANGELOG.md` updated with notable changes.

### 6.3 Process

- Prefer **small, reviewable** changes; document assumptions and fill gaps (best-guess when needed).
- Use **Mermaid** *or suggest any other one) for diagrams; keep **README.md** and **CHANGES.md** in sync with the codebase.

---

## 7. Tooling & Conventions

| Tool / Area | Use |
|-------------|-----|
| **Poetry** | Build and packaging: dependency management, `pyproject.toml`, lockfile (`poetry.lock`); install with `poetry install`, run with `poetry run`. |
| **OpenSpec** | Requirements, design, tasks; single source of truth for "what to build." |
| **Pre-commit** | Hooks for formatting, linting, and custom checks. |
| **Linters** | Python linters (e.g. Ruff, Pylint, or team choice) on commit/CI. |
| **Pytest** | Unit and integration tests; coverage reporting. |
| **Env vars** | All app-specific environment variables must use the **`FINOPS_`** prefix (e.g. `FINOPS_MASTER_ACCOUNT_ID`, `FINOPS_EXCLUDED_PROFILES`). |
| **Cursor rules** | Under `.cursor/rules/` (`.mdc`); set tone and agent-related rules. See e.g. [Cursor rules discussion](https://forum.cursor.com/best-cursor-rules-configuration/55979/5). |
| **Skills** | Add or adjust skills under `.cursor/skills/` as needed for OpenSpec and FinOps workflows. |

---

## 8. Open Questions & Gaps

- **Master/Payer account**: Exact meaning of "connect" (API, SSO, account list, tag-based filter?). To be defined in design.
- **Analysis**: Concrete list of analyses (e.g. top N services, MoM comparison, anomaly explanation) to be specified in requirements/design.
- **Frontend stack**: React + Tailwind is a candidate; confirm in Phase 2.

If you see concerns or gaps, document them here or in OpenSpec and propose best-guess assumptions where possible.

---

## 9. References

- [Strands Agents](https://strandsagents.com/latest/)
- [Spec-workflow-mcp](https://github.com/Pimzino/spec-workflow-mcp)
- OpenSpec / Spec Kit (as chosen in repo)


---

*Last updated: placeholder — update as you refine goals, requirements, and design.*
