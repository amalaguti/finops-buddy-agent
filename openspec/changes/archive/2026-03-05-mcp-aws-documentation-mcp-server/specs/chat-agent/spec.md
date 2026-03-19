# chat-agent — Delta (mcp-aws-documentation-mcp-server)

## ADDED Requirements

### Requirement: AWS Documentation MCP Server in attachable MCP set

The agent SHALL support attaching the AWS Documentation MCP Server when it is enabled via configuration. When attached, the Documentation MCP server SHALL be included in the set of MCP servers listed by `/tooling` and in the MCP server status reported by `/status`, using the same mechanism as for the AWS Knowledge MCP Server and the AWS Billing and Cost Management MCP Server.

#### Scenario: Documentation MCP appears in /tooling when enabled

- **WHEN** the AWS Documentation MCP Server is enabled and the user enters `/tooling`
- **THEN** the CLI displays the AWS Documentation MCP Server by name and the tools it provides, alongside other tools and MCP servers

#### Scenario: Documentation MCP appears in /status when enabled

- **WHEN** the AWS Documentation MCP Server is enabled and the user enters `/status`
- **THEN** the CLI includes the AWS Documentation MCP Server in the MCP server status section (e.g. ready or not ready)
