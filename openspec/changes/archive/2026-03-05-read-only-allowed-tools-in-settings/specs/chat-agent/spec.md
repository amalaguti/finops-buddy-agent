## MODIFIED Requirements

### Requirement: Read-only guardrails and friendly blocking messages

The system SHALL enforce read-only operation so the agent never produces changes to AWS infrastructure. Two guardrails SHALL apply: (1) an optional input guardrail that, when enabled, detects clearly mutating user intent before invoking the agent and responds with a single friendly message without calling the agent; (2) a mandatory tool-invocation guardrail that allows only tools on an explicit read-only allow-list to execute, and blocks any other tool call with a friendly message relayed to the user. The allow-list SHALL be the value resolved from application settings (see app-settings: when `agent.read_only_allowed_tools` is set to a non-empty list, that list is used; otherwise the application default allow-list of built-in and known MCP read-only tools is used). When either guardrail blocks a request or tool, the user SHALL see a friendly, clear message that explains what happened, why (read-only policy), and what they can do instead (e.g. ask for cost reports or use AWS Console/CLI for changes). The system prompt SHALL state that the agent must only perform read-only operations and must not create, update, or delete AWS resources; if the user asks for that, the agent SHALL explain the restriction in a friendly way.

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

#### Scenario: Tool guardrail uses configured allow-list when set

- **WHEN** the settings file sets `agent.read_only_allowed_tools` to a non-empty list (e.g. containing only `get_current_date` and `current_period_costs`)
- **THEN** only tools in that list execute; any other tool (e.g. `session-sql`) is blocked by the tool guardrail

#### Scenario: Blocked request shows friendly message

- **WHEN** either the input guardrail or the tool guardrail blocks a request
- **THEN** the text shown to the user is friendly and clear: it states what happened, why (read-only), and suggests alternatives (e.g. reports, Console/CLI); it does not use punitive or raw technical wording
