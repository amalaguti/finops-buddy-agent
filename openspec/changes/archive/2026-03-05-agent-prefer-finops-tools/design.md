# Design: Agent prefer FinOps tools (system prompt)

## Context

The chat agent in `run_chat_loop` (runner.py) builds a single `system_prompt` string and prepends it to the conversation each turn before calling the Strands agent. The prompt currently covers date limits and instructs the agent to use "the cost tools" for current month, date ranges, and comparisons. It does not guide tool choice among MCP tools. The Billing and Cost Management MCP server exposes both Cost Explorer–style tools (cost-explorer, budgets, etc.) and Billing Conductor tools (list-account-associations, list-billing-groups, etc.). The model selects by name/description and often picks Billing Conductor for "list accounts," causing permission errors for roles that have `ce:*`/`budgets:*` but not `billingconductor:*`. We cannot reorder or filter tools inside the BCM server from this repo; the only lever is the system prompt.

## Goals / Non-Goals

**Goals:**

- Reduce permission errors for account-list and cost queries by steering the agent toward Cost Explorer, Budgets, and Pricing tools.
- Keep the change localized to the system prompt string and optional README text; no new modules or tool-registry changes.

**Non-Goals:**

- Changing which MCP servers are loaded or adding a Core MCP Server; that is a separate enhancement.
- Implementing automatic retry in code when a tool returns permission denied; the prompt instructs the model to retry with alternative tools.
- Modifying MCP server code or tool descriptions.

## Decisions

1. **Extend the existing system_prompt in runner.py**  
   The prompt is built inline in `run_chat_loop`. We append 3–5 concise sentences that: (a) prefer cost-explorer, budgets, and pricing for listing accounts and cost/usage; (b) reserve Billing Conductor for explicit billing-group/custom-line-item/pro forma use cases; (c) instruct the agent to retry with those FinOps tools on permission errors when applicable. No new constants or config keys; the text is fixed in code so behavior is consistent for all users.

2. **No new settings or env vars**  
   Tool-preference text is not user-configurable. Making it configurable would add surface area without clear demand; we can add a setting later if needed.

3. **Optional README note**  
   A short note under Chat or Configuration can state that the agent prefers Cost Explorer/Budgets/Pricing for broader IAM compatibility. This is documentation only.

## Risks / Trade-offs

- **Prompt length**: Adding a few sentences increases token usage slightly per turn. Mitigation: keep the addition to 3–5 short sentences.
- **Model adherence**: The model may occasionally still choose Billing Conductor. Mitigation: the prompt also tells the model to retry with cost-explorer/budgets/pricing on permission errors, so a second tool call can recover.
- **No runtime toggle**: Users cannot disable the preference. Mitigation: the guidance is conservative (prefer common FinOps tools); we can add a setting later if someone needs to turn it off.
