# Design: Refactor runner.py into smaller modules

## Context

`runner.py` (~1,017 lines) currently contains: (1) MCP client factories and status/name helpers, (2) Strands agent construction and callbacks/hooks, (3) CLI formatters for `/tooling`, `/context`, `/credentials`, `/status`, and (4) the interactive chat loop with retries and slash commands. All live in one file. The codebase is Python/Poetry, Strands-based; CLI is the current entry point. A future FastAPI backend will need to run the same agent in a request/response fashion without the interactive loop. Splitting by responsibility keeps the public API stable while enabling the API to depend only on builder (and optionally a single-turn runner).

## Goals / Non-Goals

**Goals:**

- Reduce `runner.py` to a thin facade that re-exports `build_agent` and `run_chat_loop` (and optionally a single-turn entry for future API use).
- Introduce focused modules: MCP creation/helpers, agent builder + callbacks/hooks, CLI formatting, and chat loop.
- Preserve existing public API so `cli.py`, `agent/__init__.py`, and high-level tests keep working with minimal or no import changes.
- Make it possible for a future FastAPI app to import only builder (and single-turn execution) without pulling in the interactive loop or CLI formatters.
- Keep behavior identical: no change to user-facing features, settings, or env vars.

**Non-Goals:**

- Implementing the FastAPI backend in this change.
- Changing Strands usage, tool contracts, or MCP server configuration.
- Adding a formal “run one turn” API in this change (can be a small wrapper in `runner` or `chat_loop` later).

## Decisions

1. **Module names and locations**  
   New modules under `src/finops_agent/agent/`: `mcp.py`, `builder.py`, `format.py`, `chat_loop.py`. `runner.py` stays as the main entry module and re-exports public symbols.  
   *Rationale:* Matches the explored layout; short names and colocation with existing `tools.py` and `guardrails.py` keep the package easy to navigate.

2. **What goes where**  
   - **mcp.py**: All `create_*_mcp_client` functions, `_probe_mcp_client_readiness`, `_format_mcp_status`, `_mcp_server_name_for_tool`, `_mcp_server_names_from_tools`, `_is_tool_allowed_by_guardrail`, and MCP-related constants.  
   - **builder.py**: `build_agent`, `_create_finops_callback_handler`, `_VerboseToolDebugHook`, `_tool_source_type`, `_tool_origin`; builder imports from `mcp` and `tools`.  
   - **format.py**: `_format_tooling_output`, `_format_credentials_output`, `_format_context_output`; formatters may import from `mcp` for guardrail/status helpers.  
   - **chat_loop.py**: `run_chat_loop`, `_build_chat_system_prompt`, `_agent_used_knowledge_mcp`, `_is_rate_limit_error`, `_cleanup_agent_tools`, and the loop logic; imports from `builder`, `format`, and `mcp` as needed.  
   - **runner.py**: Imports and re-exports `build_agent`, `run_chat_loop`, and any other public or test-used symbols so existing `from finops_agent.agent.runner import ...` continue to work.  
   *Rationale:* Clear separation: MCP vs agent construction vs CLI presentation vs orchestration; API can depend on `builder` (+ optional single-turn) only.

3. **Public API surface**  
   `runner.py` remains the documented entry point. It re-exports `build_agent`, `run_chat_loop`, and any helpers that tests (e.g. `test_agent.py`) or other code currently import (e.g. `_build_chat_system_prompt`, `create_*_mcp_client`). No breaking change for callers that use `runner` only.

4. **Debug logging in the loop**  
   Remove or isolate the ad-hoc `debug-905a6f.log` (and similar) writes from the chat loop. Prefer removal; if kept, move to a small helper or feature-flag so the loop stays focused on control flow.  
   *Rationale:* Reduces noise and keeps `chat_loop.py` easier to read and test.

5. **Tests**  
   Update test imports to the new modules where tests target internals (e.g. `_format_mcp_status` → `from finops_agent.agent.mcp import ...`). Tests that only use `run_chat_loop` or `build_agent` can keep importing from `runner`.  
   *Rationale:* Preserves coverage and makes it clear which module owns which behavior.

## Risks / Trade-offs

| Risk | Mitigation |
|------|-------------|
| Circular imports between mcp ↔ builder ↔ format ↔ chat_loop | Keep dependency direction one-way: mcp (no agent deps) → builder, format → chat_loop; runner imports from all. Avoid chat_loop importing format in a way that pulls builder into a cycle. |
| Regressions in CLI or agent behavior | Run full test suite and manual smoke of chat commands; refactor is move-only plus import updates. |
| External code importing private symbols from `runner` | Re-export those symbols from `runner` so existing imports still resolve; document preferred imports (e.g. from `mcp`) in code or README. |
