# mcp-cost-explorer Specification (delta)

## REMOVED Requirements

### Requirement: AWS Cost Explorer MCP Server attachment

**Reason**: The `awslabs.cost-explorer-mcp-server` PyPI package is deprecated and yanked; attachment is no longer supported.

**Migration**: Enable `FINOPS_MCP_BILLING_ENABLED` (Billing and Cost Management MCP Server) or Core MCP with the `finops` role. See [AWS migration guide](https://github.com/awslabs/mcp/blob/main/docs/migration-cost-explorer.md).

#### Scenario: Cost Explorer MCP client included when enabled

- **WHEN** the Cost Explorer MCP server is enabled (via settings or `FINOPS_MCP_COST_EXPLORER_ENABLED`)
- **THEN** the agent is built with a Cost Explorer MCP client in its tools and can invoke that server's tools during the session

#### Scenario: Cost Explorer MCP client omitted when disabled

- **WHEN** the Cost Explorer MCP server is disabled (default or explicitly false)
- **THEN** the agent is built without the Cost Explorer MCP client and does not start the Cost Explorer MCP subprocess

### Requirement: Cost Explorer MCP configuration

**Reason**: Command and enable configuration for the removed server is replaced by deprecation handling (see ADDED requirement below).

**Migration**: Use Billing MCP settings (`FINOPS_MCP_BILLING_ENABLED`, `FINOPS_MCP_BILLING_COMMAND`).

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

**Reason**: Server is no longer attached.

**Migration**: Use `/tooling` and `/status` for Billing MCP or Core MCP instead.

#### Scenario: /tooling lists Cost Explorer MCP server and its tools

- **WHEN** the user runs `/tooling` and the Cost Explorer MCP server is enabled and attached
- **THEN** the CLI output includes a section for the AWS Cost Explorer MCP Server and lists the tools it provides (e.g. get_cost_and_usage, get_cost_forecast)

#### Scenario: /status shows Cost Explorer MCP server status

- **WHEN** the user runs `/status` and the Cost Explorer MCP server is enabled and attached
- **THEN** the CLI output includes the AWS Cost Explorer MCP Server in the MCP server status section (e.g. ready or not ready)

## ADDED Requirements

### Requirement: Cost Explorer MCP settings are deprecated

The system SHALL NOT attach the AWS Cost Explorer MCP Server. Legacy settings (`FINOPS_MCP_COST_EXPLORER_ENABLED`, `FINOPS_MCP_COST_EXPLORER_COMMAND`, and YAML equivalents) MAY still be present in user config but SHALL be ignored for agent attachment. When enable is requested (env or YAML truthy), the system SHALL log a warning that names the Billing MCP replacement and links to the AWS migration guide.

#### Scenario: Enable request logs deprecation warning and does not attach

- **WHEN** `FINOPS_MCP_COST_EXPLORER_ENABLED` is set to a truthy value
- **THEN** the agent is built without a Cost Explorer MCP client and a warning is logged directing the user to Billing MCP

#### Scenario: Default behavior unchanged

- **WHEN** Cost Explorer MCP is not enabled in config
- **THEN** no Cost Explorer MCP client is attached and no deprecation warning is logged
