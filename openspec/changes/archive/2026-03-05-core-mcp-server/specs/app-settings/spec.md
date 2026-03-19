# app-settings Specification (delta: core-mcp-server)

## ADDED Requirements

### Requirement: Resolve Core MCP enabled, command, and roles from YAML and environment

The system SHALL resolve whether the AWS Core MCP Server is enabled, which command to run, and which roles to pass to the Core subprocess from (1) the application settings file under `agent.core_mcp_enabled`, `agent.core_mcp_command`, and `agent.core_mcp_roles`, and (2) environment variables `FINOPS_MCP_CORE_ENABLED`, `FINOPS_MCP_CORE_COMMAND`, and `FINOPS_MCP_CORE_ROLES`. When `FINOPS_MCP_CORE_ENABLED` is set, it SHALL override the file value for the enabled flag. When `FINOPS_MCP_CORE_COMMAND` is set, it SHALL override the file value for the command (parsed with shlex into command and args). When `FINOPS_MCP_CORE_ROLES` is set, it SHALL override the file value for the roles (comma-separated list of role names, e.g. `finops,aws-foundation,solutions-architect`). The default for the enabled flag SHALL be false when neither file nor env is set. The default command SHALL be the project-defined uvx invocation for `awslabs.core-mcp-server` (e.g. `awslabs.core-mcp-server@latest`) with platform-specific args where applicable. The default for roles when unset SHALL be the list `[finops, aws-foundation, solutions-architect]`. The resolved enabled flag, (command, args), and list of role names SHALL be exposed to the rest of the app (e.g. agent runner).

#### Scenario: Core MCP disabled when no config

- **WHEN** the settings file has no `agent.core_mcp_enabled` and `FINOPS_MCP_CORE_ENABLED` is not set
- **THEN** the resolved Core MCP enabled flag is false

#### Scenario: Core MCP enabled via YAML

- **WHEN** the settings file sets `agent.core_mcp_enabled: true` and `FINOPS_MCP_CORE_ENABLED` is not set
- **THEN** the resolved Core MCP enabled flag is true

#### Scenario: Environment overrides YAML for Core MCP enabled

- **WHEN** the settings file sets `agent.core_mcp_enabled: true` and `FINOPS_MCP_CORE_ENABLED` is set to a falsy value (e.g. false, 0)
- **THEN** the resolved Core MCP enabled flag is false (env overrides file)

#### Scenario: Core MCP roles from default when not overridden

- **WHEN** neither the settings file nor `FINOPS_MCP_CORE_ROLES` provides a role list
- **THEN** the resolved Core MCP roles list is the default (e.g. finops, aws-foundation, solutions-architect)

#### Scenario: Core MCP roles from YAML list

- **WHEN** the settings file sets `agent.core_mcp_roles` to a list of role names (e.g. `[finops, aws-foundation, solutions-architect]`)
- **THEN** the resolved Core MCP roles list is that list (and is used to set role env vars for the Core subprocess)

#### Scenario: Core MCP roles override from environment

- **WHEN** `FINOPS_MCP_CORE_ROLES` is set to a comma-separated list (e.g. `finops,aws-foundation,solutions-architect`)
- **THEN** the resolved Core MCP roles list is the result of splitting that string (trimmed, non-empty entries) and replaces any file value

#### Scenario: Core MCP command from default when not overridden

- **WHEN** neither the settings file nor `FINOPS_MCP_CORE_COMMAND` provides a command
- **THEN** the resolved command is the default uvx invocation for awslabs.core-mcp-server (with platform-specific args if applicable)

#### Scenario: Core MCP command override from environment

- **WHEN** `FINOPS_MCP_CORE_COMMAND` is set to a valid command string (e.g. `uvx awslabs.core-mcp-server@latest`)
- **THEN** the resolved command (and args) is the result of parsing that string (e.g. via shlex) and is used to start the Core MCP server
