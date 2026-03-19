# chat-agent (delta: agent-prefer-finops-tools)

Delta spec for the chat-agent capability. Only ADDED requirements are listed; existing requirements are unchanged.

## ADDED Requirements

### Requirement: Agent system prompt prefers FinOps tools and handles permission errors

The agent's system prompt SHALL include tool-preference and permission-awareness guidance so that the agent prefers Cost Explorer, Budgets, and Pricing tools over Billing Conductor tools for account lists and general cost/usage queries. The prompt SHALL instruct the agent to use Billing Conductor tools (e.g. list-account-associations, list-billing-groups, list-custom-line-items, pricing rules/plans) only when the user explicitly asks for billing groups, custom line items, pro forma costs, or account associations in that context. The prompt SHALL instruct the agent that if a tool returns an access-denied or permission error (e.g. mentioning billingconductor), it SHALL retry the intent using cost-explorer, budgets, or pricing tools where they can answer the same question (e.g. linked accounts via cost-explorer). This improves compatibility with IAM roles that have ce:*, budgets:*, and Pricing API but not billingconductor:*.

#### Scenario: Agent prefers cost-explorer for list accounts request

- **WHEN** the user asks for a list of accounts or linked accounts and the agent has both cost-explorer and list-account-associations available
- **THEN** the agent uses the cost-explorer tool (or equivalent Cost Explorer–backed tool) to fulfill the request rather than list-account-associations, when the intent can be satisfied by account list with cost data

#### Scenario: Agent uses Billing Conductor only when explicitly needed

- **WHEN** the user asks for billing groups, custom line items, pro forma costs, or account associations in the Billing Conductor context
- **THEN** the agent MAY use Billing Conductor tools (list-account-associations, list-billing-groups, list-custom-line-items, etc.) to fulfill the request

#### Scenario: Agent retries with FinOps tools on permission error

- **WHEN** the agent calls a Billing Conductor tool and receives an access-denied or permission error (e.g. mentioning billingconductor)
- **THEN** the agent retries the same intent using cost-explorer, budgets, or pricing tools where they can answer the question (e.g. linked accounts via cost-explorer), and responds with that result or explains that the alternative was used
