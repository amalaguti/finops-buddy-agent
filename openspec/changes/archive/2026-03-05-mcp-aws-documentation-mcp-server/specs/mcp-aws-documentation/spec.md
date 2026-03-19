# mcp-aws-documentation Specification

## Purpose

Defines integration of the AWS Documentation MCP Server (awslabs.aws-documentation-mcp-server) with the chat agent: the agent can use its tools for reading and searching AWS documentation and for recommendations; the CLI exposes the server and its tools in `/tooling` and shows status in `/status`; enable/disable and command override are configurable.

## ADDED Requirements

### Requirement: AWS Documentation MCP Server attachment

The system SHALL support attaching the AWS Documentation MCP Server to the chat agent when enabled. The server SHALL be run as a local stdio subprocess (e.g. via uvx). When enabled, the agent SHALL have access to the server's tools (e.g. `read_documentation`, `search_documentation`, `recommend`). When disabled, the agent SHALL NOT start or use the Documentation MCP server.

#### Scenario: Documentation MCP client included when enabled

- **WHEN** the Documentation MCP server is enabled (via settings or `FINOPS_MCP_DOCUMENTATION_ENABLED`)
- **THEN** the agent is built with a Documentation MCP client in its tools and can invoke that server's tools during the session

#### Scenario: Documentation MCP client omitted when disabled

- **WHEN** the Documentation MCP server is disabled (default or explicitly false)
- **THEN** the agent is built without the Documentation MCP client and does not start the Documentation MCP subprocess

### Requirement: Documentation MCP configuration

The system SHALL support optional configuration for the AWS Documentation MCP Server. Configuration SHALL be loadable from the application settings file (e.g. `config/settings.yaml`) and SHALL be overridable by environment variables. All new environment variables SHALL use the `FINOPS_` prefix. At least the following SHALL be supported: an enable/disable flag (default disabled) and an optional command override (e.g. `FINOPS_MCP_DOCUMENTATION_COMMAND`) to run the server (command and args).

#### Scenario: Documentation MCP disabled by default

- **WHEN** no settings and no `FINOPS_MCP_DOCUMENTATION_ENABLED` are set
- **THEN** the Documentation MCP server is disabled and not attached to the agent

#### Scenario: Documentation MCP enabled via environment

- **WHEN** `FINOPS_MCP_DOCUMENTATION_ENABLED` is set to a truthy value (e.g. true, 1)
- **THEN** the Documentation MCP server is enabled and attached to the agent when the chat session starts

#### Scenario: Documentation MCP command override

- **WHEN** `FINOPS_MCP_DOCUMENTATION_COMMAND` (or equivalent setting) is set to a valid command string (e.g. `uvx awslabs.aws-documentation-mcp-server@latest`)
- **THEN** the system uses that command (and args) to start the Documentation MCP server instead of the default uvx command

### Requirement: Documentation MCP visibility in /tooling and /status

When the AWS Documentation MCP Server is enabled and attached to the agent, the CLI SHALL list it by a stable display name (e.g. "AWS Documentation MCP Server") in the output of `/tooling`, along with the list of tools provided by that server. The CLI SHALL include the Documentation MCP server in the MCP server status output shown for `/status` (e.g. readiness), consistent with other MCP servers.

#### Scenario: /tooling lists Documentation MCP server and its tools

- **WHEN** the user runs `/tooling` and the Documentation MCP server is enabled and attached
- **THEN** the CLI output includes a section for the AWS Documentation MCP Server and lists the tools it provides (e.g. read_documentation, search_documentation, recommend)

#### Scenario: /status shows Documentation MCP server status

- **WHEN** the user runs `/status` and the Documentation MCP server is enabled and attached
- **THEN** the CLI output includes the AWS Documentation MCP Server in the MCP server status section (e.g. ready or not ready)
