# app-settings — Delta: Pricing MCP

## ADDED Requirements

### Requirement: Resolve Pricing MCP enabled and command from YAML and environment

The system SHALL resolve whether the AWS Pricing MCP server is enabled and which command to run from (1) the application settings file under `agent.pricing_mcp_enabled` and `agent.pricing_mcp_command`, and (2) environment variables `FINOPS_MCP_PRICING_ENABLED` and `FINOPS_MCP_PRICING_COMMAND`. When `FINOPS_MCP_PRICING_ENABLED` is set, it SHALL override the file value for the enabled flag. When `FINOPS_MCP_PRICING_COMMAND` is set, it SHALL override the file value for the command (parsed with shlex into command and args). The default for the enabled flag SHALL be false when neither file nor env is set. The default command SHALL be the project-defined uvx invocation for `awslabs.aws-pricing-mcp-server` (e.g. `awslabs.aws-pricing-mcp-server@latest`) with platform-specific args where applicable. The resolved enabled flag and (command, args) SHALL be exposed to the rest of the app (e.g. agent runner).

#### Scenario: Pricing MCP disabled when no config

- **WHEN** the settings file has no `agent.pricing_mcp_enabled` and `FINOPS_MCP_PRICING_ENABLED` is not set
- **THEN** the resolved Pricing MCP enabled flag is false

#### Scenario: Pricing MCP enabled via YAML

- **WHEN** the settings file sets `agent.pricing_mcp_enabled: true` and `FINOPS_MCP_PRICING_ENABLED` is not set
- **THEN** the resolved Pricing MCP enabled flag is true

#### Scenario: Environment overrides YAML for Pricing MCP enabled

- **WHEN** the settings file sets `agent.pricing_mcp_enabled: true` and `FINOPS_MCP_PRICING_ENABLED` is set to a falsy value (e.g. false, 0)
- **THEN** the resolved Pricing MCP enabled flag is false (env overrides file)

#### Scenario: Pricing MCP command from default when not overridden

- **WHEN** neither the settings file nor `FINOPS_MCP_PRICING_COMMAND` provides a command
- **THEN** the resolved command is the default uvx invocation for awslabs.aws-pricing-mcp-server (with platform-specific args if applicable)

#### Scenario: Pricing MCP command override from environment

- **WHEN** `FINOPS_MCP_PRICING_COMMAND` is set to a valid command string (e.g. `uvx awslabs.aws-pricing-mcp-server@latest`)
- **THEN** the resolved command (and args) is the result of parsing that string (e.g. via shlex) and is used to start the Pricing MCP server
