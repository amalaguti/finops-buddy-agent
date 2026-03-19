# app-settings Specification (mcp-cost-explorer-mcp-server)

## Purpose

Define how the application loads and resolves configuration from a YAML settings file and environment variables, including Cost Explorer MCP enable/disable and command override.

## ADDED Requirements

### Requirement: Resolve Cost Explorer MCP enabled and command from YAML and environment

The system SHALL resolve whether the AWS Cost Explorer MCP server is enabled and which command to run from (1) the application settings file under `agent.cost_explorer_mcp_enabled` and `agent.cost_explorer_mcp_command`, and (2) environment variables `FINOPS_MCP_COST_EXPLORER_ENABLED` and `FINOPS_MCP_COST_EXPLORER_COMMAND`. When `FINOPS_MCP_COST_EXPLORER_ENABLED` is set, it SHALL override the file value for the enabled flag. When `FINOPS_MCP_COST_EXPLORER_COMMAND` is set, it SHALL override the file value for the command (parsed with shlex into command and args). The default for the enabled flag SHALL be false when neither file nor env is set. The default command SHALL be the project-defined uvx invocation for `awslabs.cost-explorer-mcp-server` (e.g. `awslabs.cost-explorer-mcp-server@latest`) with platform-specific args where applicable. The resolved enabled flag and (command, args) SHALL be exposed to the rest of the app (e.g. agent runner).

#### Scenario: Cost Explorer MCP disabled when no config

- **WHEN** the settings file has no `agent.cost_explorer_mcp_enabled` and `FINOPS_MCP_COST_EXPLORER_ENABLED` is not set
- **THEN** the resolved Cost Explorer MCP enabled flag is false

#### Scenario: Cost Explorer MCP enabled via YAML

- **WHEN** the settings file sets `agent.cost_explorer_mcp_enabled: true` and `FINOPS_MCP_COST_EXPLORER_ENABLED` is not set
- **THEN** the resolved Cost Explorer MCP enabled flag is true

#### Scenario: Environment overrides YAML for Cost Explorer MCP enabled

- **WHEN** the settings file sets `agent.cost_explorer_mcp_enabled: true` and `FINOPS_MCP_COST_EXPLORER_ENABLED` is set to a falsy value (e.g. false, 0)
- **THEN** the resolved Cost Explorer MCP enabled flag is false (env overrides file)

#### Scenario: Cost Explorer MCP command from default when not overridden

- **WHEN** neither the settings file nor `FINOPS_MCP_COST_EXPLORER_COMMAND` provides a command
- **THEN** the resolved command is the default uvx invocation for awslabs.cost-explorer-mcp-server (with platform-specific args if applicable)

#### Scenario: Cost Explorer MCP command override from environment

- **WHEN** `FINOPS_MCP_COST_EXPLORER_COMMAND` is set to a valid command string (e.g. `uvx awslabs.cost-explorer-mcp-server@latest`)
- **THEN** the resolved command (and args) is the result of parsing that string (e.g. via shlex) and is used to start the Cost Explorer MCP server
