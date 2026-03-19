## ADDED Requirements

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
