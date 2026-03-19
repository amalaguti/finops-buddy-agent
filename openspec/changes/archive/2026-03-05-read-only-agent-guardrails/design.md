# Read-only agent guardrails — Design

## Context

The chat agent runs in `run_chat_loop` in `runner.py`: user input is concatenated with the system prompt and conversation history, then passed to `agent(full_prompt)`. The Strands agent chooses which tools to call; there is no runtime enforcement of read-only behavior. Built-in cost tools are read-only (Cost Explorer GetCostAndUsage); MCP servers (Billing, Cost Explorer, Pricing, Documentation, Knowledge) are external and may expose both read and write tools. Project constraint: MVP is read-only AWS; all env vars use `FINOPS_` prefix.

## Goals / Non-Goals

**Goals:**

- Guarantee that no tool that can mutate AWS (or any state) ever executes: enforce via a Strands hook on `BeforeToolCallEvent` and an explicit read-only tool allow-list.
- When the user intent is clearly mutating (e.g. "create a budget"), optionally block before calling the agent and respond with a single friendly message (configurable on/off, default on).
- Whenever a guardrail blocks (input or tool), the user sees a friendly message: what happened, why (read-only policy), and what they can do (reports, Console/CLI for changes).
- System prompt states the read-only restriction so the model is less likely to attempt mutating tools; the hook remains the hard guarantee.

**Non-Goals:**

- Classifying user intent with an LLM (start with rule-based only).
- Supporting "write mode" or opt-in mutating operations in this change.
- Changing which MCP servers or tools are attached; only filtering execution by allow-list.

## Decisions

1. **Tool guardrail: allow-list (not block-list)**  
   Only tools explicitly on the read-only allow-list may run. Any tool not on the list is blocked. This is the safest: new or unknown MCP tools are blocked by default. Alternative: block-list of known mutating tool names—rejected because new mutating tools could be added by MCPs and we would not block them until we update the list.

2. **Input guardrail: rule-based (not LLM)**  
   Use keyword/phrase and simple pattern checks (e.g. mutating verbs: create, delete, update, put, set, modify, remove) to detect clearly mutating intent. Optional: treat "how do I create …?" or "what happens if I delete …?" as informational so we don’t block. Alternative: LLM classifier—rejected for latency, cost, and complexity in this change.

3. **Hook runs in process; allow-list derived from known tools**  
   The `ReadOnlyToolGuardrail` hook is registered when building the agent. The allow-list is built from (a) built-in FinOps tool names (get_current_date, current_period_costs, costs_for_date_range, month_over_month_costs, week_over_week_costs, biweekly_over_biweekly_costs), and (b) a curated list of read-only MCP tool names per server (or from config if we support override). MCP tool names may be namespaced (e.g. `aws___search_documentation`); the allow-list must use the same names the agent sees in `event.tool_use["name"]`.

4. **Friendly messages as constants / single source**  
   Define one canonical message for input-blocked and one for tool-blocked in the guardrails module (or a small messages module). Runner and hook use these so wording is consistent and easy to change. Tone: helpful, respectful; avoid punitive or technical jargon.

5. **Config: input guardrail on/off; tool guardrail always on**  
   Setting (and env) to enable/disable the input guardrail only (default: enabled). The tool guardrail is always active and not configurable off, so we never execute a non–read-only tool even if config is wrong.

## Risks / Trade-offs

- **Rule-based input guardrail can false positive/negative:** User says "how to create a budget" (informational) might be blocked, or a rephrased mutating request might slip through. Mitigation: add simple "informational" patterns (e.g. "how to", "what happens if") to reduce false positives; document that the tool guardrail is the hard guarantee.
- **MCP tool names can change:** If an MCP server renames tools, they could be blocked until we update the allow-list. Mitigation: document the allow-list and where to update it; optional config override so operators can add tool names without code change.
- **Allow-list must stay in sync with actual tools:** If we add a new built-in read-only tool and forget to add it to the allow-list, the guardrail will block it. Mitigation: derive built-in list from the same source (e.g. names of tools returned by `create_cost_tools`) or a single constant list next to the tool definitions.

## Migration Plan

- No data migration. Deploy as a normal release.
- Rollback: revert the change; agent will again have no guardrails (previous behavior).
- Feature flag: the input guardrail is effectively a feature flag via `read_only_guardrail_input_enabled`; the tool guardrail has no switch.

## Open Questions

- Whether to support configurable allow-list (YAML list of additional allowed tool names) for custom MCPs in this change or a follow-up.
