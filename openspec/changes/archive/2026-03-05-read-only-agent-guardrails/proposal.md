# Read-only agent guardrails — Proposal

## Why

The FinOps chat agent is intended to be read-only (cost/usage analysis only), but today nothing in code enforces that. A user could ask to "create a budget" or "delete X," and the agent might call a mutating tool if one is available via MCP. We need runtime guardrails so the agent never produces changes to AWS infrastructure, and when a guardrail blocks a request or tool, the user must see a friendly, clear message explaining what happened and what they can do instead.

## What Changes

- **Input guardrail (optional, configurable):** Before invoking the agent, classify the user message. If the intent is clearly mutating (e.g. create, delete, update, remove), do not call the agent; respond with a single friendly message that explains the read-only restriction and suggests alternatives (e.g. cost reports, Console/CLI for changes).
- **Tool-invocation guardrail (mandatory):** Register a Strands hook on `BeforeToolCallEvent`. Only tools on an explicit read-only allow-list may run; any other tool call is blocked and the agent receives a friendly message to relay to the user. This is the hard guarantee that no mutating tool ever executes.
- **Friendly user-facing messages:** All guardrail responses (input blocked, tool blocked) must be helpful and clear: what happened, why (read-only policy), and what the user can do (ask for reports/comparisons, use Console/CLI for changes). No raw technical or punitive wording.
- **System prompt:** Add a short line to the chat system prompt stating that the agent must only perform read-only operations and must not create, update, or delete AWS resources; if the user asks for that, explain the restriction in a friendly way.
- **Configuration:** Add a setting (and env override) to enable/disable the input guardrail (default: enabled). Tool guardrail is always on. Optionally allow extending the read-only tool allow-list via config.
- **Documentation:** Document in README that the agent is read-only, how the input and tool guardrails work, and that blocked requests receive a friendly message.

## Capabilities

### New Capabilities

None. This change only adds guardrails and messaging to the existing chat agent.

### Modified Capabilities

- **chat-agent**: Add requirements that (1) the agent SHALL enforce read-only operation via an input guardrail (when enabled) and a tool-invocation guardrail (Strands `BeforeToolCallEvent` + allow-list), and (2) when a guardrail blocks a request or tool, the user SHALL see a friendly message that explains what happened, why, and what they can do instead. System prompt SHALL state the read-only restriction.
- **app-settings**: Add agent settings for read-only guardrail (e.g. `read_only_guardrail_input_enabled`, optional allow-list override) and document any new env vars with `FINOPS_` prefix.

## Impact

- **Code:** `src/finops_agent/agent/runner.py` (chat loop: input guardrail, system prompt; agent build: add hook). New module e.g. `src/finops_agent/agent/guardrails.py` (input classification, `ReadOnlyToolGuardrail` hook, allow-list, friendly message constants).
- **Config:** `config/settings.yaml` template and settings loader for new agent guardrail options; env vars e.g. `FINOPS_READ_ONLY_GUARDRAIL_INPUT_ENABLED`.
- **Tests:** Pytest for input guardrail (mutating vs read-only intent, friendly response); pytest for tool guardrail (allowed vs disallowed tool, friendly cancel message).
- **Docs:** README configuration section updated with new settings and env vars; brief explanation of read-only behavior and friendly blocking messages.
- **Dependencies:** None new; Strands already supports hooks (`BeforeToolCallEvent`, `event.cancel_tool`).
