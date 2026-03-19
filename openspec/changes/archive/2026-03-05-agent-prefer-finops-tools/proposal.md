# Proposal: Agent prefer FinOps tools (system prompt)

## Why

When users ask for "list of accounts" or similar, the chat agent often chooses the Billing Conductor tool `list-account-associations`, which requires `billingconductor:*` IAM permissions. Many FinOps roles have Cost Explorer, Budgets, and Pricing API access (`ce:*`, `budgets:*`, pricing) but not Billing Conductor. The agent then fails with a permission error even though the same intent can be fulfilled by the `cost-explorer` tool (which returns linked accounts with cost data). We need the agent to prefer Cost Explorer, Budgets, and Pricing tools for account lists and general cost/usage queries, and to use Billing Conductor tools only when the user explicitly needs billing groups, custom line items, or pro forma costs. Fixing this via the agent's system prompt improves compatibility with typical FinOps IAM and reduces failed tool calls.

## What Changes

- Extend the chat agent's system prompt with explicit tool-preference and permission-awareness rules.
- Instruct the agent to prefer **cost-explorer**, **budgets**, and **pricing** tools for listing linked/member accounts and for cost and usage queries; use Billing Conductor tools (e.g. `list-account-associations`, `list-billing-groups`) only when the user explicitly asks for billing groups, custom line items, or pro forma costs.
- Instruct the agent that if a tool returns an access-denied or permission error (e.g. mentioning `billingconductor`), it should retry the intent using cost-explorer, budgets, or pricing tools where they can answer the same question.
- Optionally document in README that the agent prefers these tools for broader IAM compatibility.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- **chat-agent**: Add a requirement that the agent's system prompt SHALL include tool-preference and permission-awareness guidance: prefer Cost Explorer, Budgets, and Pricing tools over Billing Conductor for account lists and general cost data; use Billing Conductor only when explicitly needed; on permission errors, retry with those FinOps tools where applicable.

## Impact

- **Code**: `src/finops_agent/agent/runner.py` — extend the `system_prompt` string in `run_chat_loop` (around lines 605–612).
- **Docs**: Optional short note in README under Chat or Configuration.
- **Behavior**: No API or CLI signature changes; only the instructions sent to the LLM each turn change. Users with `ce:*`/`budgets:*` but not `billingconductor:*` will see fewer permission errors for account-list and cost queries.
