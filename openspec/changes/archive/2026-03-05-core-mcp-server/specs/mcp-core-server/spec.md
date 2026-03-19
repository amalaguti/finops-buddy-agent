# mcp-core-server Specification

## Purpose

Define how the FinOps chat agent uses the optional AWS Core MCP Server: enable/disable, role configuration (e.g. finops, aws-foundation, solutions-architect), mutual exclusion with standalone Billing, Cost Explorer, and Pricing MCP clients, disabling of built-in cost tools when Core is enabled, and exposure of Core MCP Server and its configured roles in `/tooling` and `/status` so users can see which MCP servers are loaded due to Core roles.

## Requirements

### Requirement: Core MCP Server is attachable when enabled

The agent SHALL support attaching the AWS Core MCP Server when it is enabled via configuration. The Core MCP Server SHALL be run as a local stdio process (e.g. via uvx `awslabs.core-mcp-server@latest`). When attached, the agent SHALL pass the configured role environment variables (e.g. `finops=true`, `aws-foundation=true`, `solutions-architect=true`) into the Core subprocess so that the corresponding proxied MCP servers are loaded by Core. The agent SHALL use the same AWS session (profile, region) for the Core subprocess as for other stdio MCPs (via AWS_PROFILE and AWS_REGION in the subprocess environment).

#### Scenario: Core MCP attached when enabled

- **WHEN** Core MCP is enabled in configuration and the user starts a chat session
- **THEN** the agent is built with the Core MCP client attached, and the Core subprocess is started with the configured roles in its environment

#### Scenario: Core MCP not attached when disabled

- **WHEN** Core MCP is disabled in configuration
- **THEN** the agent is built without the Core MCP client; no Core subprocess is started

### Requirement: When Core MCP is enabled, standalone Billing, Cost Explorer, and Pricing MCPs are not attached

When Core MCP is enabled, the agent SHALL NOT attach the standalone AWS Billing and Cost Management MCP client, the standalone AWS Cost Explorer MCP client, or the standalone AWS Pricing MCP client. This avoids duplicate tools, because Core’s finops role (and related roles) provide equivalent or overlapping tooling.

#### Scenario: Billing and Pricing MCP clients not attached when Core enabled

- **WHEN** Core MCP is enabled and the user has set FINOPS_MCP_BILLING_ENABLED=false and FINOPS_MCP_PRICING_ENABLED=false (or left them unset)
- **THEN** the agent is built with the Core MCP client and without the standalone Billing or Pricing MCP clients

#### Scenario: Cost Explorer MCP client not attached when Core enabled

- **WHEN** Core MCP is enabled (regardless of FINOPS_MCP_COST_EXPLORER_ENABLED)
- **THEN** the agent is built without the standalone Cost Explorer MCP client

### Requirement: Built-in cost tools disabled when Core MCP is enabled

When Core MCP is enabled, the agent SHALL NOT include the in-process built-in cost tools (e.g. current_period_costs, costs_for_date_range); only the Core MCP client (and other non-cost MCPs such as Knowledge and Documentation, when enabled) and the get_current_date tool SHALL be included. This matches the existing behavior when the Billing MCP is enabled: cost tooling is provided by the MCP server(s), not by built-in tools.

#### Scenario: Built-in cost tools omitted when Core enabled

- **WHEN** Core MCP is enabled and the agent is built
- **THEN** the agent’s tools do not include the built-in cost tools (e.g. current_period_costs, costs_for_date_range); they include get_current_date and the Core MCP tools (and any other enabled MCPs such as Knowledge, Documentation)

### Requirement: Core MCP Server and its roles shown in /tooling and /status

The CLI SHALL include the Core MCP Server in the set of MCP servers listed by `/tooling` and in the MCP server status reported by `/status`. The display name SHALL indicate the Core MCP Server and the configured roles (e.g. “Core MCP Server (roles: finops, aws-foundation, solutions-architect)”) so that users can see which MCP servers are loaded due to Core’s role configuration.

#### Scenario: Core MCP appears in /tooling with roles when enabled

- **WHEN** the Core MCP Server is enabled and the user enters `/tooling`
- **THEN** the CLI displays the Core MCP Server by a name that includes its configured roles (e.g. “Core MCP Server (roles: finops, aws-foundation, solutions-architect)”) and the tools it provides, alongside other tools and MCP servers

#### Scenario: Core MCP appears in /status with roles when enabled

- **WHEN** the Core MCP Server is enabled and the user enters `/status`
- **THEN** the CLI includes the Core MCP Server in the MCP server status section, with a name that indicates its configured roles, and reports readiness (e.g. ready (N tools) or not ready)
