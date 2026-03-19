# mcp-cost-explorer Specification

## Purpose

Defines integration of the AWS Cost Explorer MCP Server (awslabs.cost-explorer-mcp-server) with the chat agent: when enabled, the agent can use Cost Explorer–specific tools (e.g. get_cost_and_usage, get_cost_forecast). The server is optional and **disabled by default**; the BCM MCP server already covers Cost Explorer–style use cases. Enable via settings or environment for users who want the dedicated Cost Explorer MCP. The CLI exposes the server and its tools in `/tooling` and shows status in `/status`.

## Requirements

### Requirement: AWS Cost Explorer MCP Server attachment

The system SHALL support attaching the AWS Cost Explorer MCP Server to the chat agent when enabled. The server SHALL be run as a local stdio subprocess (e.g. via uvx). When enabled, the agent SHALL have access to the server's tools (e.g. get_cost_and_usage, get_cost_forecast). When disabled (default), the agent SHALL NOT start or use the Cost Explorer MCP server.

#### Scenario: Cost Explorer MCP client included when enabled

- **WHEN** the Cost Explorer MCP server is enabled (via settings or `FINOPS_MCP_COST_EXPLORER_ENABLED`)
- **THEN** the agent is built with a Cost Explorer MCP client in its tools and can invoke that server's tools during the session

#### Scenario: Cost Explorer MCP client omitted when disabled

- **WHEN** the Cost Explorer MCP server is disabled (default or explicitly false)
- **THEN** the agent is built without the Cost Explorer MCP client and does not start the Cost Explorer MCP subprocess

### Requirement: Cost Explorer MCP configuration

The system SHALL support optional configuration for the AWS Cost Explorer MCP Server. Configuration SHALL be loadable from the application settings file (e.g. `config/settings.yaml`) and SHALL be overridable by environment variables. All new environment variables SHALL use the `FINOPS_` prefix. At least the following SHALL be supported: an enable/disable flag (default **disabled**) and an optional command override (e.g. `FINOPS_MCP_COST_EXPLORER_COMMAND`) to run the server (command and args).

#### Scenario: Cost Explorer MCP disabled by default

- **WHEN** no settings and no `FINOPS_MCP_COST_EXPLORER_ENABLED` are set
- **THEN** the Cost Explorer MCP server is disabled and not attached to the agent

#### Scenario: Cost Explorer MCP enabled via environment

- **WHEN** `FINOPS_MCP_COST_EXPLORER_ENABLED` is set to a truthy value (e.g. true, 1)
- **THEN** the Cost Explorer MCP server is enabled and attached to the agent when the chat session starts

#### Scenario: Cost Explorer MCP command override

- **WHEN** `FINOPS_MCP_COST_EXPLORER_COMMAND` (or equivalent setting) is set to a valid command string (e.g. `uvx awslabs.cost-explorer-mcp-server@latest`)
- **THEN** the system uses that command (and args) to start the Cost Explorer MCP server instead of the default uvx command

### Requirement: Cost Explorer MCP visibility in /tooling and /status

When the AWS Cost Explorer MCP Server is enabled and attached to the agent, the CLI SHALL list it by a stable display name (e.g. "AWS Cost Explorer MCP Server") in the output of `/tooling`, along with the list of tools provided by that server. The CLI SHALL include the Cost Explorer MCP server in the MCP server status output shown for `/status` (e.g. readiness), consistent with other MCP servers.

#### Scenario: /tooling lists Cost Explorer MCP server and its tools

- **WHEN** the user runs `/tooling` and the Cost Explorer MCP server is enabled and attached
- **THEN** the CLI output includes a section for the AWS Cost Explorer MCP Server and lists the tools it provides (e.g. get_cost_and_usage, get_cost_forecast)

#### Scenario: /status shows Cost Explorer MCP server status

- **WHEN** the user runs `/status` and the Cost Explorer MCP server is enabled and attached
- **THEN** the CLI output includes the AWS Cost Explorer MCP Server in the MCP server status section (e.g. ready or not ready)
