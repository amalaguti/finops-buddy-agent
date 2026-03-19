# Chat Agent (Strands) — Design

## Context

The FinOps CLI currently provides imperative commands (whoami, profiles, context, costs, verify). There is no conversational interface. The project has chosen Strands Agents as the AI framework (Phase 1: “Agent (Strands) integrated for assistant-style interaction”). Existing code provides: AWS session resolution (profile, identity), current-month cost retrieval by service (`get_costs_by_service`), and table formatting. The agent must support multi-turn chat and cost analysis (past, current, MoM, WoW, biweekly-over-biweekly) and be structured so that tools can later be backed by local AWS MCP servers (Cost Explorer, Billing & Cost Management, etc.) without re-architecting.

Constraints: Python 3.10+, Poetry, FINOPS_ prefix for all app env vars, read-only AWS usage, CLI-only for this change.

## Goals / Non-Goals

**Goals:**

- Expose a CLI subcommand (e.g. `finops chat`) that starts an interactive Strands-based chat session.
- Support multi-turn conversations: user input → agent response → repeat until exit.
- Enable the agent to analyze and investigate costs: past costs, current costs, and comparisons (month-over-month, week-over-week, biweekly-over-biweekly), using tools that can be implemented first with existing cost/session logic and later backed by MCP.
- Use the Strands Agents library for agent lifecycle, tool binding, and LLM calls (e.g. Bedrock).
- Keep the agent layer MCP-ready (tool interface and wiring so that MCP servers can be added in a follow-up change).

**Non-Goals:**

- Implementing or connecting local AWS MCP servers in this change (deferred to a later change).
- Backend API or web UI for the agent (CLI only).
- Persistence of conversation history across sessions (in-scope can be in-memory for the session only).

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **CLI entrypoint** | Add a `chat` subcommand (e.g. `finops chat [--profile NAME]`) | Clear, consistent with existing subcommands; profile flows from root or subparser. |
| **Agent library** | Use `strands-agents` (PyPI: `strands-agents`) | Aligns with PROJECT_CONTEXT; AWS-native, model-agnostic, built-in tool/MCP support for future. |
| **Model / runtime** | Default to Strands’ default (e.g. Bedrock); allow override via `FINOPS_AGENT_MODEL_ID` or settings | Keeps AWS alignment; optional override for testing or different models. |
| **Tool design** | Implement FinOps tools (current costs, date-range costs, MoM/WoW/biweekly comparison) as Strands tools in this repo; same tool interface can later call MCP when MCP servers are added | Delivers cost-analysis behavior now; clear path to MCP without rewriting agent. |
| **Session / credentials** | Reuse existing `get_session(profile_name=...)` and pass profile from CLI; agent or tools use this session for Cost Explorer (and later MCP can use same profile context) | Single source of profile resolution; read-only CE calls. |
| **Module layout** | New package or module under `src/finops_agent/` (e.g. `agent/` with `__init__.py`, agent builder, and tool definitions) | Keeps agent code grouped and testable; CLI imports and invokes agent. |
| **Configuration** | Optional agent settings in `config/settings.yaml` (e.g. `agent.model_id`) and env `FINOPS_AGENT_MODEL_ID`; document in README | FINOPS_ prefix; one place for defaults. |

**Alternatives considered:**

- **Other agent frameworks**: Rejected; PROJECT_CONTEXT mandates Strands.
- **Chat vs agent subcommand name**: “chat” preferred for user-facing clarity; implementation can still be “agent” internally.
- **Tools-only vs MCP-first**: Implement tools in code first so cost analysis works without MCP; add MCP in a follow-up so we don’t block on MCP setup.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Strands API or dependency churn | Pin `strands-agents` version in Poetry; add tests that assert agent starts and one round-trip. |
| Cost Explorer rate limits or latency in chat | Tools should remain read-only and use existing bounded CE calls; if needed, add short caching in a later change. |
| Large token usage in long sessions | Document that session is in-memory; optional future cap on history length. |
| MCP integration later requires refactor | Design tools with a thin “adapter” layer (e.g. same tool names, implementation swaps to MCP client when available). |

## Migration Plan

- Add dependency and new code behind the `chat` subcommand; no changes to existing commands or config schema beyond adding optional agent keys.
- No data migration. Rollback: remove `chat` subcommand and agent module; revert dependency.

## Open Questions

- Exact Strands API for “run loop” (read user input, invoke agent, print response) to be confirmed during implementation (docs or quickstart).
- Whether to support streaming output in the first version or only full-message response (implementation detail; can default to non-streaming for simplicity).
