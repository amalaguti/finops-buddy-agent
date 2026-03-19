## 1. Branch and setup

- [x] 1.1 Create a feature branch (e.g. `feature/chat-agent-strands` or `FT/chat-agent-strands`); do not implement on `main`. Switch to that branch before implementing.
- [x] 1.2 Add `strands-agents` as a dependency in `pyproject.toml` (Poetry) and run `poetry lock` / `poetry install`.
- [x] 1.3 Create agent module layout under `src/finops_agent/` (e.g. `agent/` package with `__init__.py`, and modules for agent builder and tools).

## 2. Configuration

- [x] 2.1 Add optional agent settings to the app settings schema (e.g. `agent.model_id`) and support loading them in the settings module; ensure any new env var uses the `FINOPS_` prefix (e.g. `FINOPS_AGENT_MODEL_ID`).
- [x] 2.2 Add or update `config/settings.yaml` as template: include agent-related keys (e.g. `agent.model_id`) with sample/placeholder or commented values; keep file safe to commit.
- [x] 2.3 Document new agent settings and `FINOPS_AGENT_MODEL_ID` in README.md (Configuration / Settings and environment section).

## 3. Cost tools

- [x] 3.1 Implement a cost-tools layer (Strands-compatible) that uses the resolved AWS session: tool for current-period costs (reuse or wrap `get_costs_by_service`), tool for costs in a given date range, and helpers for MoM / WoW / biweekly date ranges.
- [x] 3.2 Expose tools for month-over-month, week-over-week, and biweekly-over-biweekly comparisons (each returns cost data for two consecutive periods so the agent can summarize).
- [x] 3.3 Register these tools with the Strands agent so cost-related user questions invoke the appropriate tool(s).

## 4. Strands agent and chat loop

- [x] 4.1 Build the Strands agent (model from config/env default or `FINOPS_AGENT_MODEL_ID`), attach the cost tools, and use the resolved profile/session for tool execution.
- [x] 4.2 Implement the interactive chat loop: prompt for user input, send to agent, display response, repeat until exit (e.g. `/quit` or EOF); maintain in-memory conversation context for the session.

## 5. CLI integration

- [x] 5.1 Add a `chat` subcommand to the CLI (e.g. `finops chat [--profile NAME]`); ensure `--profile` / `-p` works on the chat subparser and from the root parser.
- [x] 5.2 Wire the chat subcommand to the agent chat loop so that `finops chat` and `finops chat --profile X` start the session with the correct profile.

## 6. Lint, format, and tests

- [x] 6.1 Run `poetry run ruff check .` and `poetry run ruff format .`; fix any reported issues.
- [x] 6.2 Add or extend pytest unit tests: one test per spec scenario (WHEN/THEN) where practical; place tests in `tests/` (e.g. `tests/test_agent.py`, `tests/test_chat_cli.py`); name tests after the scenario (e.g. `test_chat_starts_with_default_profile`, `test_agent_uses_tools_for_cost_queries`).
