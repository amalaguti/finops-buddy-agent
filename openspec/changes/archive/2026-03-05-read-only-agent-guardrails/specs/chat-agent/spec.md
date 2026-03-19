# chat-agent — Delta spec (read-only-agent-guardrails)

## ADDED Requirements

### Requirement: Read-only guardrails and friendly blocking messages

The system SHALL enforce read-only operation so the agent never produces changes to AWS infrastructure. Two guardrails SHALL apply: (1) an optional input guardrail that, when enabled, detects clearly mutating user intent before invoking the agent and responds with a single friendly message without calling the agent; (2) a mandatory tool-invocation guardrail that allows only tools on an explicit read-only allow-list to execute, and blocks any other tool call with a friendly message relayed to the user. When either guardrail blocks a request or tool, the user SHALL see a friendly, clear message that explains what happened, why (read-only policy), and what they can do instead (e.g. ask for cost reports or use AWS Console/CLI for changes). The system prompt SHALL state that the agent must only perform read-only operations and must not create, update, or delete AWS resources; if the user asks for that, the agent SHALL explain the restriction in a friendly way.

#### Scenario: Input guardrail blocks clearly mutating request when enabled

- **WHEN** the input guardrail is enabled and the user enters a message that is classified as clearly mutating (e.g. create, delete, update a resource)
- **THEN** the agent is not invoked, and the user sees a friendly message that explains the read-only restriction and suggests alternatives (e.g. cost reports, Console/CLI for changes)

#### Scenario: Input guardrail allows read-only request

- **WHEN** the input guardrail is enabled and the user enters a message that is not classified as mutating (e.g. "What did we spend last month?")
- **THEN** the message is sent to the agent and the agent responds as usual

#### Scenario: Tool guardrail blocks disallowed tool

- **WHEN** the agent attempts to invoke a tool that is not on the read-only allow-list
- **THEN** the tool is not executed and the agent receives a friendly message to relay to the user explaining that the action cannot be run (read-only policy) and what the user can do instead

#### Scenario: Tool guardrail allows tool on allow-list

- **WHEN** the agent attempts to invoke a tool that is on the read-only allow-list
- **THEN** the tool executes normally and its result is used in the agent response

#### Scenario: Blocked request shows friendly message

- **WHEN** either the input guardrail or the tool guardrail blocks a request
- **THEN** the text shown to the user is friendly and clear: it states what happened, why (read-only), and suggests alternatives (e.g. reports, Console/CLI); it does not use punitive or raw technical wording

## MODIFIED Requirements

### Requirement: Agent system prompt prefers FinOps tools and handles permission errors

The agent's system prompt SHALL include tool-preference and permission-awareness guidance so that the agent prefers Cost Explorer for listing linked/member accounts (with account IDs and names) and uses the cost-explorer tool for that purpose rather than the budgets tool or Billing Conductor. The prompt SHALL instruct the agent not to use the budgets tool for a simple list of accounts; use budgets only when the user asks about budgets (e.g. budget configurations, alerts, or amounts). The prompt SHALL instruct the agent to use Billing Conductor tools (e.g. list-account-associations, list-billing-groups, list-custom-line-items, pricing rules/plans) only when the user explicitly asks for billing groups, custom line items, pro forma costs, or account associations in that context. The prompt SHALL instruct the agent that if a tool returns an access-denied or permission error (e.g. mentioning billingconductor), it SHALL retry the intent using cost-explorer or pricing tools where they can answer the same question (e.g. linked accounts via cost-explorer). This improves compatibility with IAM roles that have ce:* and budgets:* but not billingconductor:*. The prompt SHALL also state that the agent must only perform read-only operations and must not create, update, or delete any AWS resources; if the user asks for such actions, the agent SHALL explain in a friendly way that it is restricted to read-only and suggest alternatives (e.g. cost reports, AWS Console or CLI for changes).

#### Scenario: Agent prefers cost-explorer for list accounts request

- **WHEN** the user asks for a list of accounts or linked accounts and the agent has both cost-explorer and list-account-associations available
- **THEN** the agent uses the cost-explorer tool (or equivalent Cost Explorer–backed tool) to fulfill the request rather than list-account-associations or budgets, when the intent can be satisfied by account list with cost data

#### Scenario: Agent uses Billing Conductor only when explicitly needed

- **WHEN** the user asks for billing groups, custom line items, pro forma costs, or account associations in the Billing Conductor context
- **THEN** the agent MAY use Billing Conductor tools (list-account-associations, list-billing-groups, list-custom-line-items, etc.) to fulfill the request

#### Scenario: Agent retries with FinOps tools on permission error

- **WHEN** the agent calls a Billing Conductor tool and receives an access-denied or permission error (e.g. mentioning billingconductor)
- **THEN** the agent retries the same intent using cost-explorer or pricing tools where they can answer the question (e.g. linked accounts via cost-explorer), and responds with that result or explains that the alternative was used
