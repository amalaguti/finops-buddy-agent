# Agent module structure

## ADDED Requirements

### Requirement: Agent package SHALL be split into focused modules

The agent package SHALL provide separate modules for MCP client creation and helpers, agent building and callbacks, CLI formatting, and the interactive chat loop. A thin runner module SHALL re-export the public API so existing callers can continue to import `build_agent` and `run_chat_loop` from a single entry point.

#### Scenario: Public API remains importable from runner

- **WHEN** code imports `build_agent` or `run_chat_loop` from `finops_agent.agent.runner`
- **THEN** the import succeeds and the returned functions are the same as before the refactor (behavior unchanged)

#### Scenario: MCP logic is isolated in its own module

- **WHEN** MCP client creation or MCP-related helpers (e.g. probe readiness, server names, guardrail allow-list checks) are needed
- **THEN** such logic SHALL live in a dedicated module (e.g. `mcp.py`) and SHALL NOT be duplicated in the chat loop or builder

#### Scenario: Agent building is isolated and reusable

- **WHEN** an agent instance is built with cost tools and optional MCP clients
- **THEN** the construction logic SHALL live in a dedicated module (e.g. `builder.py`) so that a future FastAPI backend can import only this module (and dependencies) without importing the interactive chat loop or CLI formatters

#### Scenario: CLI formatting is isolated

- **WHEN** output for `/tooling`, `/context`, `/credentials`, or `/status` is produced
- **THEN** the formatting logic SHALL live in a dedicated module (e.g. `format.py`) used by the chat loop, not in the same file as the loop control flow

#### Scenario: Chat loop is a single entry for interactive use

- **WHEN** the interactive chat loop runs (prompt, agent call, slash commands, retries)
- **THEN** the loop SHALL live in a dedicated module (e.g. `chat_loop.py`) that uses the builder and formatters, and SHALL NOT contain MCP client factory implementations or agent construction logic
