# Read-only agent guardrails — Tasks

Implement on a **feature branch** (e.g. `feature/read-only-agent-guardrails`). Do not implement on `main`.

## 1. Settings and configuration

- [x] 1.1 Add `agent.read_only_guardrail_input_enabled` to the settings schema and loader (default true); add `FINOPS_READ_ONLY_GUARDRAIL_INPUT_ENABLED` env override; expose getter for use by the runner.
- [x] 1.2 Update `config/settings.yaml` template with the new key under `agent:` (e.g. `read_only_guardrail_input_enabled: true`) and a short comment; use placeholder/sample values only.

## 2. Guardrails module

- [x] 2.1 Create `src/finops_agent/agent/guardrails.py` with constants for the two friendly messages (input-blocked, tool-blocked): what happened, why read-only, what the user can do; tone helpful and clear.
- [x] 2.2 In `guardrails.py`, implement a rule-based input classifier: normalize user input (lowercase, strip), detect clearly mutating intent (e.g. verbs: create, delete, update, put, set, modify, remove; optionally treat "how to …", "what happens if …" as informational). Expose a function e.g. `is_mutating_intent(text: str) -> bool`.
- [x] 2.3 In `guardrails.py`, define the read-only tool allow-list: built-in FinOps tool names (get_current_date, current_period_costs, costs_for_date_range, month_over_month_costs, week_over_week_costs, biweekly_over_biweekly_costs) plus a curated list of read-only MCP tool names (per design; use actual names as seen by the agent, including namespaced forms if any).
- [x] 2.4 In `guardrails.py`, implement `ReadOnlyToolGuardrail` (Strands `HookProvider`): register callback for `BeforeToolCallEvent`; if `event.tool_use["name"]` is not in the allow-list, set `event.cancel_tool` to the friendly tool-blocked message.

## 3. Runner integration

- [x] 3.1 In `run_chat_loop`, after handling `/tooling`, `/context`, `/credentials`, `/status` and before appending to conversation and calling the agent: when the input guardrail is enabled, call the input classifier; if mutating, print the friendly input-blocked message, append it as the agent response to the conversation, and continue the loop without calling the agent.
- [x] 3.2 In `build_agent` (and wherever the agent is built with tools), add `ReadOnlyToolGuardrail(allowed_tools=...)` to the agent's `hooks` list so the tool guardrail runs on every tool call.
- [x] 3.3 In `_build_chat_system_prompt`, add a short line stating that the agent must only perform read-only operations and must not create, update, or delete AWS resources; if the user asks for that, explain the restriction in a friendly way and suggest alternatives.

## 4. Documentation and tests

- [x] 4.1 Document in README.md: agent read-only behavior; that the input guardrail (when enabled) and tool guardrail block mutating requests/tools; that blocked requests receive a friendly message; document `FINOPS_READ_ONLY_GUARDRAIL_INPUT_ENABLED` and the YAML key `agent.read_only_guardrail_input_enabled` in the Configuration / Settings section.
- [x] 4.2 Run `poetry run ruff check .` and `poetry run ruff format .`; fix any issues.
- [x] 4.3 Add or extend pytest: test that when input guardrail is enabled and user message is mutating, the agent is not called and a friendly message is returned (message mentions read-only and suggests alternatives); test that when message is not mutating, the agent is called; test that when a disallowed tool is invoked (mock BeforeToolCallEvent), `cancel_tool` is set to the friendly message; test that when an allowed tool is invoked, `cancel_tool` is not set. Place tests in `tests/` (e.g. `test_guardrails.py`, `test_agent.py` or existing chat/runner tests as appropriate); name tests after the spec scenarios.
