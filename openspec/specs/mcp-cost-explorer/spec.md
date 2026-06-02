# mcp-cost-explorer Specification

## Purpose

Documents legacy Cost Explorer MCP settings and their deprecation. The standalone AWS Cost Explorer MCP Server (`awslabs.cost-explorer-mcp-server`) PyPI package is **deprecated and yanked**; FinOps Buddy **does not attach** this server. Use the **Billing and Cost Management MCP Server** (`FINOPS_MCP_BILLING_ENABLED`) or Core MCP with the `finops` role for Cost Explorer functionality. See the [AWS migration guide](https://github.com/awslabs/mcp/blob/main/docs/migration-cost-explorer.md).

## Requirements

### Requirement: Cost Explorer MCP settings are deprecated

The system SHALL NOT attach the AWS Cost Explorer MCP Server. Legacy settings (`FINOPS_MCP_COST_EXPLORER_ENABLED`, `FINOPS_MCP_COST_EXPLORER_COMMAND`, and YAML equivalents) MAY still be present in user config but SHALL be ignored for agent attachment. When enable is requested (env or YAML truthy), the system SHALL log a warning that names the Billing MCP replacement and links to the AWS migration guide.

#### Scenario: Enable request logs deprecation warning and does not attach

- **WHEN** `FINOPS_MCP_COST_EXPLORER_ENABLED` is set to a truthy value
- **THEN** the agent is built without a Cost Explorer MCP client and a warning is logged directing the user to Billing MCP

#### Scenario: Default behavior unchanged

- **WHEN** Cost Explorer MCP is not enabled in config
- **THEN** no Cost Explorer MCP client is attached and no deprecation warning is logged
