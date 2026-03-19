# mcp-aws-pricing Specification

## Purpose

Defines integration of the AWS Pricing MCP Server (awslabs.aws-pricing-mcp-server) with the chat agent: when enabled, the agent can use Pricing MCP tools for real-time AWS pricing discovery, cost reports, multi-region comparisons, CDK/Terraform project scan, and cost optimization recommendations. The server is optional and **disabled by default**. The CLI exposes the server and its tools in `/tooling` and shows status in `/status`.

## Requirements

### Requirement: AWS Pricing MCP Server attachment

The system SHALL support attaching the AWS Pricing MCP Server to the chat agent when enabled. The server SHALL be run as a local stdio subprocess (e.g. via uvx). When enabled, the agent SHALL have access to the server's tools (e.g. service catalog exploration, pricing attribute discovery, real-time pricing queries, cost report generation, project scan). When disabled (default), the agent SHALL NOT start or use the Pricing MCP server.

#### Scenario: Pricing MCP client included when enabled

- **WHEN** the Pricing MCP server is enabled (via settings or `FINOPS_MCP_PRICING_ENABLED`)
- **THEN** the agent is built with a Pricing MCP client in its tools and can invoke that server's tools during the session

#### Scenario: Pricing MCP client omitted when disabled

- **WHEN** the Pricing MCP server is disabled (default or explicitly false)
- **THEN** the agent is built without the Pricing MCP client and does not start the Pricing MCP subprocess

### Requirement: Pricing MCP configuration

The system SHALL support optional configuration for the AWS Pricing MCP Server. Configuration SHALL be loadable from the application settings file (e.g. `config/settings.yaml`) and SHALL be overridable by environment variables. All new environment variables SHALL use the `FINOPS_` prefix. At least the following SHALL be supported: an enable/disable flag (default **disabled**) and an optional command override (e.g. `FINOPS_MCP_PRICING_COMMAND`) to run the server (command and args).

#### Scenario: Pricing MCP disabled by default

- **WHEN** no settings and no `FINOPS_MCP_PRICING_ENABLED` are set
- **THEN** the Pricing MCP server is disabled and not attached to the agent

#### Scenario: Pricing MCP enabled via environment

- **WHEN** `FINOPS_MCP_PRICING_ENABLED` is set to a truthy value (e.g. true, 1)
- **THEN** the Pricing MCP server is enabled and attached to the agent when the chat session starts

#### Scenario: Pricing MCP command override

- **WHEN** `FINOPS_MCP_PRICING_COMMAND` (or equivalent setting) is set to a valid command string (e.g. `uvx awslabs.aws-pricing-mcp-server@latest`)
- **THEN** the system uses that command (and args) to start the Pricing MCP server instead of the default uvx command

### Requirement: Pricing MCP visibility in /tooling and /status

When the AWS Pricing MCP Server is enabled and attached to the agent, the CLI SHALL list it by a stable display name (e.g. "AWS Pricing MCP Server") in the output of `/tooling`, along with the list of tools provided by that server. The CLI SHALL include the Pricing MCP server in the MCP server status output shown for `/status` (e.g. readiness), consistent with other MCP servers.

#### Scenario: /tooling lists Pricing MCP server and its tools

- **WHEN** the user runs `/tooling` and the Pricing MCP server is enabled and attached
- **THEN** the CLI output includes a section for the AWS Pricing MCP Server and lists the tools it provides (e.g. service catalog, pricing queries, cost reports, project scan)

#### Scenario: /status shows Pricing MCP server status

- **WHEN** the user runs `/status` and the Pricing MCP server is enabled and attached
- **THEN** the CLI output includes the AWS Pricing MCP Server in the MCP server status section (e.g. ready or not ready)
