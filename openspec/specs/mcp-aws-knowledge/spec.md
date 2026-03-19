# mcp-aws-knowledge Specification

## Purpose

Define how the FinOps chat agent uses the remote AWS Knowledge MCP Server to access up-to-date AWS documentation, API references, best practices, and regional availability, and how the CLI exposes this capability in `/tooling` and informs the user when the agent has consulted AWS Knowledge.

## Requirements

### Requirement: Agent uses remote AWS Knowledge MCP Server

The chat agent SHALL be able to call tools provided by the remote AWS Knowledge MCP Server (e.g. `search_documentation`, `read_documentation`, `recommend`, `list_regions`, `get_regional_availability`) when the server is enabled and reachable. The server SHALL be contacted via Streamable HTTP at a configurable URL (default `https://knowledge-mcp.global.api.aws`). The agent SHALL combine these tools with existing built-in cost tools in a single agent session.

#### Scenario: Agent can use AWS Knowledge MCP tools when enabled

- **WHEN** the AWS Knowledge MCP Server is enabled in configuration and the remote server is reachable
- **THEN** the agent is built with both built-in cost tools and the Knowledge MCP tools, and can answer questions that require AWS documentation or regional availability (e.g. "What regions support Cost Explorer?")

#### Scenario: Agent runs without Knowledge MCP when disabled or unreachable

- **WHEN** the Knowledge MCP is disabled in configuration or the remote server is unreachable
- **THEN** the agent still starts and works with the existing built-in cost tools only; no failure or crash

### Requirement: /tooling lists AWS Knowledge MCP Server and its tools

When the user enters `/tooling`, the CLI SHALL display the AWS Knowledge MCP Server by name (e.g. "AWS Knowledge MCP Server") and SHALL list the tools provided by that server (e.g. search_documentation, read_documentation, recommend, list_regions, get_regional_availability), in addition to built-in tools. The display SHALL allow the user to see that these tools come from the MCP server and what they do.

#### Scenario: User sees AWS Knowledge MCP Server and its tools in /tooling

- **WHEN** the user enters `/tooling` at the chat prompt and the AWS Knowledge MCP Server is enabled
- **THEN** the CLI displays a section or grouping for the AWS Knowledge MCP Server and the list of tools it provides (with names and, when available, descriptions)

### Requirement: User is informed when agent consulted AWS Knowledge

When the agent has used at least one tool from the AWS Knowledge MCP Server to produce a response, the CLI SHALL inform the user with a short, visible message (e.g. "Consulted AWS Knowledge for this response.") so that the user knows the MCP server was contacted for that turn.

#### Scenario: User sees notification when agent used AWS Knowledge

- **WHEN** the agent returns a response and at least one tool call in that turn was to a tool from the AWS Knowledge MCP Server
- **THEN** the CLI displays a brief message indicating that AWS Knowledge was consulted for that response (e.g. before or after the agent reply)

#### Scenario: No notification when agent did not use AWS Knowledge

- **WHEN** the agent returns a response and no tool from the AWS Knowledge MCP Server was used in that turn
- **THEN** the CLI does not display the "Consulted AWS Knowledge" message for that response

### Requirement: AWS Knowledge MCP configuration

The system SHALL support optional configuration to enable or disable the AWS Knowledge MCP Server and to override its URL. Any new environment variables SHALL use the `FINOPS_` prefix (e.g. `FINOPS_KNOWLEDGE_MCP_ENABLED`, `FINOPS_KNOWLEDGE_MCP_URL`). Configuration SHALL be documented in README and reflected in `config/settings.yaml` as the template for app settings.

#### Scenario: Knowledge MCP can be enabled or disabled via configuration

- **WHEN** the user sets the appropriate FINOPS_ configuration (e.g. FINOPS_KNOWLEDGE_MCP_ENABLED) to true or false
- **THEN** the agent includes or excludes the AWS Knowledge MCP Server tools accordingly when starting the chat session

#### Scenario: Knowledge MCP URL can be overridden

- **WHEN** the user sets FINOPS_KNOWLEDGE_MCP_URL (or equivalent in settings) to a valid Streamable HTTP MCP endpoint
- **THEN** the agent connects to that URL for the AWS Knowledge MCP Server instead of the default
