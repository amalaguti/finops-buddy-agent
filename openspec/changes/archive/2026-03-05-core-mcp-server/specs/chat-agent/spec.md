# chat-agent Specification (delta: core-mcp-server)

## ADDED Requirements

### Requirement: AWS Core MCP Server in attachable MCP set with mutual exclusion

The agent SHALL support attaching the AWS Core MCP Server when it is enabled via configuration. When Core MCP is enabled, the agent SHALL attach the Core MCP client and SHALL NOT attach the standalone Billing and Cost Management, Cost Explorer, or Pricing MCP clients; built-in cost tools SHALL be omitted (see mcp-core-server spec). When Core MCP is disabled, the agent SHALL behave as today (Billing, Cost Explorer, Pricing attachable independently; built-in cost tools included when Billing is not attached). When attached, the Core MCP server SHALL be included in the set of MCP servers listed by `/tooling` and in the MCP server status reported by `/status`, with a display name that indicates the configured roles so users can see which MCP servers are loaded due to Core roles.

#### Scenario: Core MCP appears in /tooling with roles when enabled

- **WHEN** the Core MCP Server is enabled and the user enters `/tooling`
- **THEN** the CLI displays the Core MCP Server with a name that includes its configured roles (e.g. “Core MCP Server (roles: finops, aws-foundation, solutions-architect)”) and the tools it provides, alongside other tools and MCP servers

#### Scenario: Core MCP appears in /status with roles when enabled

- **WHEN** the Core MCP Server is enabled and the user enters `/status`
- **THEN** the CLI includes the Core MCP Server in the MCP server status section with a name that indicates its configured roles and reports readiness (e.g. ready (N tools) or not ready)

#### Scenario: Standalone Billing and Pricing not attached when Core enabled

- **WHEN** Core MCP is enabled (regardless of FINOPS_MCP_BILLING_ENABLED or FINOPS_MCP_PRICING_ENABLED)
- **THEN** the agent is built with the Core MCP client and without the standalone Billing or Pricing MCP clients; /tooling does not list the standalone Billing or Pricing MCP servers

#### Scenario: Startup progress includes Core MCP when enabled

- **WHEN** the user runs `finops chat` and Core MCP is enabled
- **THEN** the CLI emits a progress message for the Core MCP Server as it is loaded (e.g. “Loading Core MCP…”)
