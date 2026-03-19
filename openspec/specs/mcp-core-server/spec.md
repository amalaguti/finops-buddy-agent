# mcp-core-server Specification

## Purpose

Define how the FinOps chat agent uses the optional AWS Core MCP Server: enable/disable, role configuration (e.g. finops, aws-foundation, solutions-architect), optional co-loading with standalone Billing, Cost Explorer, and Pricing MCP clients, and exposure of Core MCP Server and its configured roles in `/tooling` and `/status` so users can see which MCP servers are loaded due to Core roles.

## Requirements

### Requirement: Core MCP Server is attachable when enabled

The agent SHALL support attaching the AWS Core MCP Server when it is enabled via configuration. The Core MCP Server SHALL be run as a local stdio process (e.g. via uvx `awslabs.core-mcp-server@latest`). When attached, the agent SHALL pass the configured role environment variables (e.g. `finops=true`, `aws-foundation=true`, `solutions-architect=true`) into the Core subprocess so that the corresponding proxied MCP servers are loaded by Core. The agent SHALL use the same AWS session (profile, region) for the Core subprocess as for other stdio MCPs (via AWS_PROFILE and AWS_REGION in the subprocess environment).

#### Scenario: Core MCP attached when enabled

- **WHEN** Core MCP is enabled in configuration and the user starts a chat session
- **THEN** the agent is built with the Core MCP client attached, and the Core subprocess is started with the configured roles in its environment

#### Scenario: Core MCP not attached when disabled

- **WHEN** Core MCP is disabled in configuration
- **THEN** the agent is built without the Core MCP client; no Core subprocess is started

### Requirement: Core MCP can load together with Billing, Cost Explorer, and Pricing MCPs

When Core MCP is enabled, the agent MAY also attach the standalone AWS Billing and Cost Management MCP client, the standalone AWS Cost Explorer MCP client, and the standalone AWS Pricing MCP client when they are enabled in configuration. There SHALL be no mutual exclusion: Core and these MCPs can all be attached in the same session. The agent's system prompt SHALL instruct that when the Core MCP Server is available and does not produce a complete, satisfactory, or accurate result for the user's request, the agent SHALL use the other MCP servers (e.g. AWS Billing and Cost Management, Cost Explorer, Pricing) to provide a complete response.

#### Scenario: Billing and Core both attached when both enabled

- **WHEN** Core MCP and Billing MCP are both enabled in configuration
- **THEN** the agent is built with both the Core MCP client and the standalone Billing MCP client attached; /tooling lists both

#### Scenario: Agent uses other MCPs when Core result incomplete

- **WHEN** the Core MCP Server is available and the user asks for cost optimization or savings and Core does not produce a complete or satisfactory result
- **THEN** the agent uses the other MCP servers (e.g. cost-optimization, compute-optimizer from Billing MCP) to provide a complete response

### Requirement: Built-in cost tools omitted when Billing MCP is present

When the Billing MCP client is attached (whether or not Core is enabled), the agent SHALL NOT include the in-process built-in cost tools (e.g. current_period_costs, costs_for_date_range); only get_current_date and the MCP-provided tools SHALL be included. When Billing is not attached, built-in cost tools SHALL be included (and Core MCP, when enabled, may also be attached).

#### Scenario: Built-in cost tools omitted when Billing MCP present

- **WHEN** the Billing MCP client is attached and the agent is built
- **THEN** the agent's tools do not include the built-in cost tools; they include get_current_date and the tools from attached MCPs (e.g. Core, Billing, Cost Explorer, Pricing)

### Requirement: Core MCP Server and its roles shown in /tooling and /status

The CLI SHALL include the Core MCP Server in the set of MCP servers listed by `/tooling` and in the MCP server status reported by `/status`. The display name SHALL indicate the Core MCP Server and the configured roles (e.g. "Core MCP Server (roles: finops, aws-foundation, solutions-architect)") so that users can see which MCP servers are loaded due to Core's role configuration.

#### Scenario: Core MCP appears in /tooling with roles when enabled

- **WHEN** the Core MCP Server is enabled and the user enters `/tooling`
- **THEN** the CLI displays the Core MCP Server by a name that includes its configured roles (e.g. "Core MCP Server (roles: finops, aws-foundation, solutions-architect)") and the tools it provides, alongside other tools and MCP servers

#### Scenario: Core MCP appears in /status with roles when enabled

- **WHEN** the Core MCP Server is enabled and the user enters `/status`
- **THEN** the CLI includes the Core MCP Server in the MCP server status section, with a name that indicates its configured roles, and reports readiness (e.g. ready (N tools) or not ready)
