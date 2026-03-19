# Refactor runner.py into smaller modules

## Why

`src/finops_agent/agent/runner.py` is ~1,017 lines and mixes several concerns: MCP client creation, agent building, CLI formatting, callbacks/hooks, and the interactive chat loop. This makes the file hard to maintain and test. A future FastAPI backend will need to reuse agent building and single-turn execution without the interactive loop; keeping everything in one file would force the API to depend on a large, CLI-coupled module. Splitting now establishes clear boundaries (MCP, builder, formatting, chat loop) and makes it straightforward to add an API that depends only on builder + one-turn execution.

## What Changes

- **Split `runner.py`** into focused modules under `src/finops_agent/agent/`:
  - **MCP**: Factory functions and helpers for creating MCP clients, probing readiness, and resolving server names (e.g. `mcp.py`).
  - **Builder**: Agent construction, callback handler, and hooks (e.g. `builder.py`).
  - **Formatting**: CLI-oriented formatters for `/tooling`, `/context`, `/credentials`, `/status` (e.g. `format.py`).
  - **Chat loop**: Interactive loop only—prompt, agent call, commands, retries (e.g. `chat_loop.py`).
  - **Runner**: Thin facade that re-exports public API (`build_agent`, `run_chat_loop`) and optionally exposes a single-turn entry point for future API use.
- **Preserve public API**: `run_chat_loop` and `build_agent` remain the primary entry points; callers (CLI, `agent/__init__.py`, tests) continue to import from `runner` or from the new facade so existing usage does not break.
- **Tests**: Update test imports to target the new modules where they test internals; keep or add tests so behavior is unchanged.
- **Remove or isolate** ad-hoc debug logging in the chat loop (e.g. `debug-905a6f.log`) so the loop stays focused on flow control.

No change to user-facing behavior, settings, or environment variables. **BREAKING** only if external code relies on importing private symbols from `runner` (e.g. `_format_mcp_status`); we will keep such symbols available via `runner` re-exports or document the new import paths.

## Capabilities

### New Capabilities

- `agent-module-structure`: Describes the desired layout of the agent package (MCP, builder, formatting, chat loop, runner facade) for maintainability, testability, and readiness for a future FastAPI backend that reuses builder and single-turn execution.

### Modified Capabilities

- None. The chat-agent capability’s requirements are unchanged; only the implementation structure changes.

## Impact

- **Code**: `src/finops_agent/agent/runner.py` reduced to a thin layer; new files `mcp.py`, `builder.py`, `format.py`, `chat_loop.py` (or equivalent names). Existing `tools.py` and `guardrails.py` unchanged.
- **Imports**: `cli.py`, `agent/__init__.py`, and tests may import from `runner` (facade) or directly from new modules; internal imports within the agent package updated to use new modules.
- **Dependencies**: No new runtime dependencies. Future FastAPI routes can depend on builder (and optionally a `run_one_turn`-style function) without pulling in the interactive chat loop or CLI formatters.
