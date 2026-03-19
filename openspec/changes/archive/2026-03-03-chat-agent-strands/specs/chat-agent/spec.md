# chat-agent Specification

## Purpose

Defines the Strands-based chat agent exposed via the CLI: multi-turn conversations and cost analysis (past, current, month-over-month, week-over-week, biweekly-over-biweekly), with an MCP-ready tool design for future local AWS MCP server integration.

## ADDED Requirements

### Requirement: CLI chat subcommand

The CLI SHALL provide a `chat` subcommand that starts an interactive Strands-based agent session. The command SHALL accept an optional `--profile` (or `-p`) for AWS profile selection, consistent with other subcommands. When invoked, the CLI SHALL start a read-eval-print loop: prompt for user input, send input to the agent, display the agent’s response, and repeat until the user exits (e.g. by a reserved command or EOF).

#### Scenario: Chat starts with default profile

- **WHEN** the user runs `finops chat` with no profile specified
- **THEN** the CLI starts the Strands agent session using the default credential chain (e.g. AWS_PROFILE or default profile) and displays a prompt for the first user message

#### Scenario: Chat starts with named profile

- **WHEN** the user runs `finops chat --profile my-account` (or `finops --profile my-account chat`)
- **THEN** the CLI starts the Strands agent session using profile `my-account` and displays a prompt for the first user message

#### Scenario: Chat session accepts input and returns response

- **WHEN** the user enters a message at the chat prompt and the agent processes it
- **THEN** the CLI displays the agent’s response and prompts again for the next message

### Requirement: Multi-turn conversation

The agent SHALL support multi-turn conversations: it SHALL maintain conversation context for the duration of the session (in-memory) and SHALL use the Strands Agents library for agent lifecycle and LLM invocation. The agent SHALL produce coherent, context-aware responses across turns.

#### Scenario: Follow-up question uses prior context

- **WHEN** the user asks a follow-up question that refers to a previous message in the same session
- **THEN** the agent’s response SHALL be consistent with the prior context (e.g. same account, time range, or topic)

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

The agent’s cost-related capabilities SHALL be implemented via a tool layer (Strands tools) that can be backed either by in-process logic (e.g. existing `get_costs_by_service` and date-range helpers) or, in a future change, by local AWS MCP servers. The tool interface (names, parameters, return shape) SHALL be defined so that the same agent can use MCP-backed implementations without changing the agent’s prompt or control flow.

#### Scenario: Agent uses tools for cost queries

- **WHEN** the user asks a cost-related question (e.g. “What did we spend last month?”)
- **THEN** the agent invokes the appropriate tool(s) and incorporates the tool results into its response

### Requirement: Agent configuration

The system SHALL support optional agent configuration. Agent-related settings SHALL be loadable from the application settings file (e.g. `config/settings.yaml`) and SHALL be overridable by environment variables. Any new environment variables SHALL use the `FINOPS_` prefix (e.g. `FINOPS_AGENT_MODEL_ID` for model override). If no model is configured, the system SHALL use the Strands default (e.g. Bedrock).

#### Scenario: Agent runs with default model when no config set

- **WHEN** no agent model is configured (no setting and no `FINOPS_AGENT_MODEL_ID`)
- **THEN** the agent starts using the Strands default model (e.g. Bedrock) and can process at least one user message

#### Scenario: Agent respects model override from environment

- **WHEN** `FINOPS_AGENT_MODEL_ID` is set to a valid model identifier
- **THEN** the agent uses that model for LLM calls when starting the chat session
