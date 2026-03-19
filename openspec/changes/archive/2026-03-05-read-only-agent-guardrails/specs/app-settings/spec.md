# app-settings — Delta spec (read-only-agent-guardrails)

## ADDED Requirements

### Requirement: Resolve read-only guardrail settings from YAML and environment

The system SHALL resolve read-only guardrail settings from (1) the application settings file under `agent.read_only_guardrail_input_enabled`, and (2) environment variable `FINOPS_READ_ONLY_GUARDRAIL_INPUT_ENABLED`. When `FINOPS_READ_ONLY_GUARDRAIL_INPUT_ENABLED` is set, it SHALL override the file value. The input guardrail SHALL be enabled by default when neither file nor env is set. The resolved value SHALL be exposed to the agent (e.g. runner) so that the input guardrail runs only when enabled. Any new environment variables SHALL use the `FINOPS_` prefix. Optionally, the system MAY support an override for the read-only tool allow-list (e.g. `agent.read_only_allowed_tools` or a path) so operators can extend the list without code changes; if supported, it SHALL be documented in the configuration section of the README.

#### Scenario: Input guardrail enabled by default when no config

- **WHEN** the settings file has no `agent.read_only_guardrail_input_enabled` and `FINOPS_READ_ONLY_GUARDRAIL_INPUT_ENABLED` is not set
- **THEN** the resolved input guardrail enabled flag is true

#### Scenario: Input guardrail disabled via YAML

- **WHEN** the settings file sets `agent.read_only_guardrail_input_enabled: false` and `FINOPS_READ_ONLY_GUARDRAIL_INPUT_ENABLED` is not set
- **THEN** the resolved input guardrail enabled flag is false and the input guardrail does not run

#### Scenario: Environment overrides YAML for input guardrail

- **WHEN** the settings file sets `agent.read_only_guardrail_input_enabled: false` and `FINOPS_READ_ONLY_GUARDRAIL_INPUT_ENABLED` is set to a truthy value (e.g. true, 1)
- **THEN** the resolved input guardrail enabled flag is true (env overrides file)
