# chat-agent Specification

## Purpose

Defines the Strands-based chat agent exposed via the CLI: multi-turn conversations and cost analysis (past, current, month-over-month, week-over-week, biweekly-over-biweekly), with an MCP-ready tool design for future local AWS MCP server integration.

## Requirements

### Requirement: CLI chat subcommand

The CLI SHALL provide a `chat` subcommand that starts an interactive Strands-based agent session. The command SHALL accept an optional `--profile` (or `-p`) for AWS profile selection, consistent with other subcommands. When invoked, the CLI SHALL start a read-eval-print loop: prompt for user input, send input to the agent, display the agent's response, and repeat until the user exits (e.g. by a reserved command or EOF).

#### Scenario: Chat starts with default profile

- **WHEN** the user runs `finops chat` with no profile specified
- **THEN** the CLI starts the Strands agent session using the default credential chain (e.g. AWS_PROFILE or default profile) and displays a prompt for the first user message

#### Scenario: Chat starts with named profile

- **WHEN** the user runs `finops chat --profile my-account` (or `finops --profile my-account chat`)
- **THEN** the CLI starts the Strands agent session using profile `my-account` and displays a prompt for the first user message

#### Scenario: Chat session accepts input and returns response

- **WHEN** the user enters a message at the chat prompt and the agent processes it
- **THEN** the CLI displays the agent's response and prompts again for the next message

### Requirement: Multi-turn conversation

The agent SHALL support multi-turn conversations: it SHALL maintain conversation context for the duration of the session (in-memory) and SHALL use the Strands Agents library for agent lifecycle and LLM invocation. The agent SHALL produce coherent, context-aware responses across turns.

#### Scenario: Follow-up question uses prior context

- **WHEN** the user asks a follow-up question that refers to a previous message in the same session
- **THEN** the agent's response SHALL be consistent with the prior context (e.g. same account, time range, or topic)

### Requirement: Cost analysis capabilities

The agent SHALL be able to analyze and investigate costs by using tools (or equivalent) that provide: (1) current-period costs (e.g. current month by service), (2) past costs for a given date range, (3) month-over-month comparison, (4) week-over-week comparison, and (5) biweekly-over-biweekly comparison. Tools SHALL use the resolved AWS session (profile) and SHALL perform only read-only operations (e.g. Cost Explorer GetCostAndUsage).

#### Scenario: Agent can report current-period costs

- **WHEN** the user asks for current-month (or current-period) costs
- **THEN** the agent uses the available cost tooling to retrieve and summarize costs for the current period (e.g. by service) and responds with that information

#### Scenario: Agent can report month-over-month comparison

- **WHEN** the user asks for a month-over-month cost comparison
- **THEN** the agent uses the available tooling to retrieve costs for two consecutive months and responds with a comparison (e.g. change, trend)

#### Scenario: Agent can report week-over-week comparison

- **WHEN** the user asks for a week-over-week cost comparison
- **THEN** the agent uses the available tooling to retrieve costs for two consecutive weeks and responds with a comparison

#### Scenario: Agent can report biweekly-over-biweekly comparison

- **WHEN** the user asks for a biweekly-over-biweekly cost comparison
- **THEN** the agent uses the available tooling to retrieve costs for two consecutive biweekly periods and responds with a comparison

### Requirement: MCP-ready tool design

The agent's cost-related capabilities SHALL be implemented via a tool layer (Strands tools) that can be backed either by in-process logic (e.g. existing `get_costs_by_service` and date-range helpers) or, in a future change, by local AWS MCP servers. The tool interface (names, parameters, return shape) SHALL be defined so that the same agent can use MCP-backed implementations without changing the agent's prompt or control flow.

#### Scenario: Agent uses tools for cost queries

- **WHEN** the user asks a cost-related question (e.g. "What did we spend last month?")
- **THEN** the agent invokes the appropriate tool(s) and incorporates the tool results into its response

### Requirement: AWS Documentation MCP Server in attachable MCP set

The agent SHALL support attaching the AWS Documentation MCP Server when it is enabled via configuration. When attached, the Documentation MCP server SHALL be included in the set of MCP servers listed by `/tooling` and in the MCP server status reported by `/status`, using the same mechanism as for the AWS Knowledge MCP Server and the AWS Billing and Cost Management MCP Server.

#### Scenario: Documentation MCP appears in /tooling when enabled

- **WHEN** the AWS Documentation MCP Server is enabled and the user enters `/tooling`
- **THEN** the CLI displays the AWS Documentation MCP Server by name and the tools it provides, alongside other tools and MCP servers

#### Scenario: Documentation MCP appears in /status when enabled

- **WHEN** the AWS Documentation MCP Server is enabled and the user enters `/status`
- **THEN** the CLI includes the AWS Documentation MCP Server in the MCP server status section (e.g. ready or not ready)

### Requirement: User informed when agent used AWS Knowledge MCP

When the agent has used at least one tool from the AWS Knowledge MCP Server to produce a response for the current turn, the CLI SHALL inform the user with a short, visible message (e.g. "Consulted AWS Knowledge for this response.") so that the user knows the MCP server was contacted. When no tool from the AWS Knowledge MCP Server was used for that response, the CLI SHALL NOT display this message.

#### Scenario: Notification shown when agent used AWS Knowledge MCP

- **WHEN** the agent returns a response and at least one tool call in that turn was to a tool from the AWS Knowledge MCP Server
- **THEN** the CLI displays a brief message indicating that AWS Knowledge was consulted for that response

#### Scenario: No notification when agent did not use AWS Knowledge MCP

- **WHEN** the agent returns a response and no tool from the AWS Knowledge MCP Server was used in that turn
- **THEN** the CLI does not display the "Consulted AWS Knowledge" message for that response

### Requirement: Agent configuration

The system SHALL support optional agent configuration. Agent-related settings SHALL be loadable from the application settings file (e.g. `config/settings.yaml`) and SHALL be overridable by environment variables. Any new environment variables SHALL use the `FINOPS_` prefix (e.g. `FINOPS_AGENT_MODEL_ID` for model override). If no model is configured, the system SHALL use the Strands default (e.g. Bedrock).

#### Scenario: Agent runs with default model when no config set

- **WHEN** no agent model is configured (no setting and no `FINOPS_AGENT_MODEL_ID`)
- **THEN** the agent starts using the Strands default model (e.g. Bedrock) and can process at least one user message

#### Scenario: Agent respects model override from environment

- **WHEN** `FINOPS_AGENT_MODEL_ID` is set to a valid model identifier
- **THEN** the agent uses that model for LLM calls when starting the chat session

### Requirement: Reserved meta-commands /tooling and /context

The chat loop SHALL treat the user inputs `/tooling` and `/context` as reserved commands. When the user enters `/tooling`, the CLI SHALL display internal tooling information: the list of available tools (and skills, if any), their purpose, and when they are used. The displayed tooling information SHALL include MCP servers by name (e.g. "AWS Knowledge MCP Server") and the tools they provide, in addition to built-in tools. For each tool, when the tool is blocked by the read-only guardrail, the CLI SHALL append ` (blocked)` to the tool name in the listing. The CLI SHALL also display a YAML example block for `agent.read_only_allowed_tools` that lists all tools shown in the session; blocked tools SHALL have ` (blocked)` appended to their name in the YAML. The YAML block SHALL be valid and ready to copy into the settings file. When the user enters `/context`, the CLI SHALL display conversation context status: number of turns, current profile, session identity, token counts (when available from the model/runtime), and model-specific state or info (e.g. model ID, provider). Both commands SHALL be handled in the chat loop before sending input to the agent; the agent SHALL NOT receive `/tooling` or `/context` as user messages. No LLM call SHALL be made for these commands. Command matching SHALL be case-insensitive and SHALL ignore leading and trailing whitespace. The response SHALL be printed to the user and the loop SHALL prompt for the next input without appending the meta-command or its response to the conversation history.

#### Scenario: User enters /tooling and sees available tools

- **WHEN** the user enters `/tooling` (or `/Tooling` or `  /tooling  `) at the chat prompt
- **THEN** the CLI displays a human-readable summary of the agent's available tools (names and descriptions, including when each is used), does not call the LLM, and prompts again for the next message

#### Scenario: User enters /tooling and sees MCP servers and their tools

- **WHEN** the user enters `/tooling` at the chat prompt and one or more MCP servers (e.g. AWS Knowledge MCP Server) are enabled
- **THEN** the CLI displays each MCP server by name and the list of tools provided by that server, in addition to built-in tools, and prompts again for the next message

#### Scenario: Blocked tools show (blocked) suffix in /tooling listing

- **WHEN** the user enters `/tooling` and at least one tool is blocked by the read-only guardrail
- **THEN** each blocked tool's name in the listing has ` (blocked)` appended (e.g. `create_budget (blocked)`)

#### Scenario: /tooling displays YAML example for read_only_allowed_tools

- **WHEN** the user enters `/tooling` at the chat prompt
- **THEN** the CLI displays a YAML example block for `agent.read_only_allowed_tools` that lists all tools shown in the session, with blocked tools having ` (blocked)` appended to their name, in valid YAML format ready to copy into the settings file

#### Scenario: User enters /context and sees conversation context status

- **WHEN** the user enters `/context` (or `/Context` or `  /context  `) at the chat prompt
- **THEN** the CLI displays conversation context status (e.g. number of turns, current AWS profile, session/account info, token counts and model-specific state when available), does not call the LLM, and prompts again for the next message

#### Scenario: Meta-commands are not sent to the agent

- **WHEN** the user enters `/tooling` or `/context`
- **THEN** that input is not appended to the conversation history and is not sent to the agent as a user message

#### Scenario: Chat welcome or docs mention meta-commands

- **WHEN** the user starts a chat session or consults the documented chat commands
- **THEN** `/tooling` and `/context` are documented (e.g. in the welcome message or README) as available commands alongside `/quit`

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

### Requirement: Startup progress display

The chat subcommand SHALL display incremental progress messages during initialization so the user is informed while credentials are resolved, cost tools are created, MCP servers are loaded, and the agent is built. Progress messages SHALL be emitted to stderr. Each major step (e.g. resolving credentials, loading each MCP server, building agent) SHALL produce a short, human-readable message (e.g. "Resolving credentials...", "Loading AWS Knowledge MCP...", "Ready."). The CLI SHALL support an optional `--quiet` flag on the chat subcommand; when `--quiet` is set, the CLI SHALL NOT display startup progress messages.

#### Scenario: Progress shown during chat startup

- **WHEN** the user runs `finops chat` (without `--quiet`) and initialization begins
- **THEN** the CLI emits progress messages to stderr for each major step (e.g. credentials, cost tools, MCP servers, agent build) before displaying the welcome message and prompt

#### Scenario: Progress includes MCP server names when loading

- **WHEN** the user runs `finops chat` and one or more MCP servers are enabled (e.g. AWS Knowledge, Billing, Documentation)
- **THEN** the CLI emits a progress message for each MCP server as it is loaded (e.g. "Loading AWS Knowledge MCP...", "Loading Billing MCP...")

#### Scenario: Quiet mode suppresses startup progress

- **WHEN** the user runs `finops chat --quiet` (or `finops chat -q` if short form is supported)
- **THEN** the CLI does not emit startup progress messages to stderr; the user sees only the welcome message and prompt once initialization completes

### Requirement: AWS Core MCP Server in attachable MCP set

The agent SHALL support attaching the AWS Core MCP Server when it is enabled via configuration. When Core MCP is enabled, the agent SHALL attach the Core MCP client and MAY also attach the standalone Billing, Cost Explorer, and Pricing MCP clients when they are enabled (no mutual exclusion). When attached, the Core MCP server SHALL be included in the set of MCP servers listed by `/tooling` and in the MCP server status reported by `/status`, with a display name that indicates the configured roles so users can see which MCP servers are loaded due to Core roles. The system prompt SHALL instruct that when Core MCP is available and does not produce a complete, satisfactory, or accurate result, the agent SHALL use the other MCP servers (e.g. AWS Billing and Cost Management, Cost Explorer, Pricing) to provide a complete response.

#### Scenario: Core MCP appears in /tooling with roles when enabled

- **WHEN** the Core MCP Server is enabled and the user enters `/tooling`
- **THEN** the CLI displays the Core MCP Server with a name that includes its configured roles (e.g. "Core MCP Server (roles: finops, aws-foundation, solutions-architect)") and the tools it provides, alongside other tools and MCP servers

#### Scenario: Core MCP appears in /status with roles when enabled

- **WHEN** the Core MCP Server is enabled and the user enters `/status`
- **THEN** the CLI includes the Core MCP Server in the MCP server status section with a name that indicates its configured roles and reports readiness (e.g. ready (N tools) or not ready)

#### Scenario: Startup progress includes Core MCP when enabled

- **WHEN** the user runs `finops chat` and Core MCP is enabled
- **THEN** the CLI emits a progress message for the Core MCP Server as it is loaded (e.g. "Loading Core MCP…")

### Requirement: OpenAI model parameter compatibility

When using the OpenAI provider (FINOPS_OPENAI_API_KEY set), the agent SHALL pass completion-token parameters in a format supported by the configured model. Newer OpenAI models (e.g. gpt-5.x, o1) require `max_completion_tokens` instead of `max_tokens`. The agent SHALL use `max_completion_tokens` (or the appropriate parameter for the model) so that users can configure any supported OpenAI model via `FINOPS_AGENT_MODEL_ID` without API parameter errors.

#### Scenario: Agent starts with newer OpenAI model requiring max_completion_tokens

- **WHEN** `FINOPS_OPENAI_API_KEY` is set, `FINOPS_AGENT_MODEL_ID` is set to a model that requires `max_completion_tokens` (e.g. gpt-5.4, o1), and the user starts a chat session
- **THEN** the agent starts successfully and can process at least one user message without a 400 "Unsupported parameter: max_tokens" error

#### Scenario: Agent starts with legacy OpenAI model

- **WHEN** `FINOPS_OPENAI_API_KEY` is set, `FINOPS_AGENT_MODEL_ID` is set to a legacy model (e.g. gpt-4o) or unset (default gpt-4o), and the user starts a chat session
- **THEN** the agent starts successfully and can process at least one user message
