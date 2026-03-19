# app-settings Specification

## Purpose

Define how the application loads and resolves configuration from a YAML settings file and environment variables, with dotenv support so that `.env` and `.env.local` can supply or override values. Resolved settings (e.g. excluded profiles list) are exposed to the rest of the app.

## Requirements

### Requirement: Load app settings from YAML

The system SHALL load app configuration from an optional YAML settings file. The default path SHALL be `$XDG_CONFIG_HOME/finops-agent/settings.yaml`, or `~/.config/finops-agent/settings.yaml` when `XDG_CONFIG_HOME` is unset. An optional environment variable `FINOPS_CONFIG_FILE` SHALL override this path when set. If the file is missing, the system SHALL treat it as "no settings" (e.g. empty excluded list). Invalid YAML SHALL be handled by logging and falling back to empty or env-only resolution.

#### Scenario: Default XDG path is used when FINOPS_CONFIG_FILE is unset

- **WHEN** the user runs the app and `FINOPS_CONFIG_FILE` is not set
- **THEN** the system looks for settings at `$XDG_CONFIG_HOME/finops-agent/settings.yaml` (or `~/.config/finops-agent/settings.yaml` if `XDG_CONFIG_HOME` is unset)

#### Scenario: Custom config path is used when FINOPS_CONFIG_FILE is set

- **WHEN** `FINOPS_CONFIG_FILE` is set (e.g. to a repo-local path)
- **THEN** the system loads settings from that path instead of the default XDG path

#### Scenario: Missing or invalid YAML does not fail the app

- **WHEN** the settings file is missing or contains invalid YAML
- **THEN** the system proceeds with no file-based defaults (e.g. empty excluded list) or env-only values; the app SHALL NOT exit due to missing or invalid YAML

### Requirement: Resolve excluded profiles from YAML and environment

The system SHALL resolve the excluded-profiles list from (1) YAML defaults (e.g. key `excluded_profiles`), and (2) environment variable `FINOPS_EXCLUDED_PROFILES` (comma-separated). When `FINOPS_EXCLUDED_PROFILES` is set, it SHALL replace the entire list from YAML (no merge). The resolved list SHALL be exposed to the rest of the app (e.g. for filtering profile listings).

#### Scenario: YAML-only excluded list is used when env is unset

- **WHEN** the YAML file exists and defines `excluded_profiles` and `FINOPS_EXCLUDED_PROFILES` is not set
- **THEN** the resolved excluded list is the list from the YAML file

#### Scenario: Environment overrides YAML excluded list

- **WHEN** both YAML and `FINOPS_EXCLUDED_PROFILES` are set
- **THEN** the resolved excluded list is the comma-separated list from the environment (env replaces the entire YAML list)

#### Scenario: No exclusions when neither YAML nor env provide a list

- **WHEN** the settings file is missing or has no excluded_profiles, and `FINOPS_EXCLUDED_PROFILES` is not set
- **THEN** the resolved excluded list is empty (no profiles excluded)

### Requirement: Resolve included-only profiles from YAML and environment

The system SHALL resolve an optional **included-only-profiles** list from (1) YAML settings (key `included_only_profiles`, list of strings), and (2) environment variable `FINOPS_INCLUDED_ONLY_PROFILES` (comma-separated). When `FINOPS_INCLUDED_ONLY_PROFILES` is set, it SHALL replace the entire list from YAML (no merge). The resolved list SHALL be exposed to the rest of the app (e.g. for filtering profile listings). When the resolved list is **non-empty**, allowlist mode is active: only profiles in this list are in scope. When the list is **empty or absent**, the existing excluded-profiles (blocklist) behavior SHALL apply. At most one of allowlist or blocklist is active: if included_only_profiles is non-empty, it takes precedence; otherwise excluded_profiles is used.

#### Scenario: YAML-only included list is used when env is unset

- **WHEN** the YAML file exists and defines `included_only_profiles` and `FINOPS_INCLUDED_ONLY_PROFILES` is not set
- **THEN** the resolved included-only list is the list from the YAML file

#### Scenario: Environment overrides YAML included-only list

- **WHEN** both YAML and `FINOPS_INCLUDED_ONLY_PROFILES` are set
- **THEN** the resolved included-only list is the comma-separated list from the environment (env replaces the entire YAML list)

#### Scenario: No allowlist when neither YAML nor env provide included_only

- **WHEN** the settings file is missing or has no `included_only_profiles`, and `FINOPS_INCLUDED_ONLY_PROFILES` is not set
- **THEN** the resolved included-only list is empty (allowlist mode is off; excluded_profiles blocklist applies if set)

#### Scenario: Empty included list means blocklist mode

- **WHEN** the resolved included_only_profiles list is empty
- **THEN** the app uses excluded_profiles (blocklist) for profile filtering, if any

### Requirement: Load dotenv so .env.local overrides all other sources

The system SHALL load environment variables from `.env` and then from `.env.local` at startup (e.g. at CLI entrypoint). Loading `.env.local` SHALL use `override=True` so that values in `.env.local` override those from `.env` and any pre-existing shell environment. This ensures `.env.local` wins over all other sources for app configuration.

#### Scenario: .env.local overrides .env

- **WHEN** both `.env` and `.env.local` exist and define the same variable (e.g. `FINOPS_EXCLUDED_PROFILES`)
- **THEN** the value from `.env.local` is used after dotenv load

#### Scenario: Missing .env or .env.local does not error

- **WHEN** `.env` or `.env.local` is missing
- **THEN** the system loads the existing file(s) only; missing files SHALL NOT cause the app to fail

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

### Requirement: Resolve read-only allowed tools from YAML

The system SHALL resolve the read-only tool allow-list from the application settings file under `agent.read_only_allowed_tools` (YAML list of strings, each a tool name). When this key is present and is a non-empty list, the resolved allow-list SHALL be exactly that list (as a set) and SHALL be exposed to the read-only tool guardrail. When the key is absent, not a list, or an empty list, the system SHALL use the application default allow-list (built-in FinOps tools plus known MCP read-only tool names). No environment variable SHALL override this setting; configuration is file-only for the allow-list.

#### Scenario: Default allow-list when key is absent

- **WHEN** the settings file has no `agent.read_only_allowed_tools` (or the key is missing)
- **THEN** the resolved allow-list is the application default (built-in + known MCP read-only tools)

#### Scenario: Default allow-list when key is empty list

- **WHEN** the settings file sets `agent.read_only_allowed_tools: []`
- **THEN** the resolved allow-list is the application default (built-in + known MCP read-only tools)

#### Scenario: Custom allow-list when key is non-empty list

- **WHEN** the settings file sets `agent.read_only_allowed_tools` to a non-empty list of tool names (e.g. `["get_current_date", "current_period_costs", "session-sql"]`)
- **THEN** the resolved allow-list is exactly that set of names and is used by the read-only tool guardrail

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

### Requirement: Resolve agent warm-on-startup from YAML and environment

The system SHALL resolve whether to warm up the chat agent at API startup from (1) the application settings file under `agent.warm_on_startup` (boolean), and (2) environment variable `FINOPS_AGENT_WARM_ON_STARTUP`. When `FINOPS_AGENT_WARM_ON_STARTUP` is set to a truthy value (`1`, `true`, `yes`, case-insensitive), it SHALL enable warm-up. When set to a falsy value (`0`, `false`, `no`, empty), it SHALL disable warm-up. When the env var is set, it SHALL override the file value. The default for the warm-up flag SHALL be **true** when neither file nor env is set. The resolved flag SHALL be exposed to the API startup code.

#### Scenario: Warm-up enabled by default when no config

- **WHEN** the settings file has no `agent.warm_on_startup` and `FINOPS_AGENT_WARM_ON_STARTUP` is not set
- **THEN** the resolved warm-on-startup flag is true (warm-up happens by default)

#### Scenario: Warm-up enabled via YAML

- **WHEN** the settings file sets `agent.warm_on_startup: true` and `FINOPS_AGENT_WARM_ON_STARTUP` is not set
- **THEN** the resolved warm-on-startup flag is true

#### Scenario: Warm-up disabled via YAML

- **WHEN** the settings file sets `agent.warm_on_startup: false` and `FINOPS_AGENT_WARM_ON_STARTUP` is not set
- **THEN** the resolved warm-on-startup flag is false (warm-up is skipped)

#### Scenario: Environment overrides YAML to enable warm-up

- **WHEN** the settings file sets `agent.warm_on_startup: false` and `FINOPS_AGENT_WARM_ON_STARTUP` is set to `true`
- **THEN** the resolved warm-on-startup flag is true (env overrides file)

#### Scenario: Environment overrides YAML to disable warm-up

- **WHEN** the settings file sets `agent.warm_on_startup: true` and `FINOPS_AGENT_WARM_ON_STARTUP` is set to `false`
- **THEN** the resolved warm-on-startup flag is false (env overrides file)

#### Scenario: Empty environment variable uses YAML value

- **WHEN** the settings file sets `agent.warm_on_startup: false` and `FINOPS_AGENT_WARM_ON_STARTUP` is set to empty string
- **THEN** the resolved warm-on-startup flag is false (empty env is treated as unset, YAML value is used)
