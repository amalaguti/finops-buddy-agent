# app-settings (delta)

## ADDED Requirements

### Requirement: Resolve cloud deployment mode from YAML and environment

The system SHALL resolve **cloud deployment mode** from (1) YAML settings under a documented key (e.g. `deployment.cloud_mode` or equivalent), and (2) environment variable `FINOPS_CLOUD_DEPLOYMENT_MODE` (or a single documented boolean env). When the environment variable is set, it SHALL override the YAML value. When cloud deployment mode is **true**, downstream modules SHALL use the cloud identity rules from the aws-identity capability; when **false** or unset, local profile behavior SHALL apply. The README and `config/settings.yaml` template SHALL document the key and env var.

#### Scenario: Environment enables cloud mode over YAML

- **WHEN** YAML sets cloud deployment mode to false and `FINOPS_CLOUD_DEPLOYMENT_MODE` is set to a **true** value per documented parsing rules
- **THEN** the resolved cloud deployment mode is **true**

#### Scenario: YAML enables cloud mode when env unset

- **WHEN** YAML sets cloud deployment mode to true and `FINOPS_CLOUD_DEPLOYMENT_MODE` is unset
- **THEN** the resolved cloud deployment mode is **true**

### Requirement: Resolve FinOps target map from YAML and environment

When cloud deployment mode is enabled, the system SHALL resolve a **FinOps target map** from (1) YAML under a documented structure (e.g. list of objects with `id`, `role_arn`, optional display name), and (2) an optional `FINOPS_ASSUMABLE_TARGETS_JSON` env var that **replaces** the YAML map when set (no merge). Invalid JSON in the env var SHALL be handled by logging and treating the map as **empty** or by failing fast with a clear startup error per documented behavior. README and `config/settings.yaml` SHALL show **placeholder** account ids and role ARNs only.

#### Scenario: Env replaces YAML map when set

- **WHEN** YAML defines targets and `FINOPS_ASSUMABLE_TARGETS_JSON` is set to valid JSON
- **THEN** the resolved target map comes **only** from the environment variable

#### Scenario: Invalid env JSON does not silently merge partial YAML

- **WHEN** `FINOPS_ASSUMABLE_TARGETS_JSON` is set but invalid
- **THEN** the system follows documented behavior (clear error at startup or empty map with log) and does not use partial data as if it were valid

### Requirement: Resolve trusted reverse-proxy auth and group allowlist

The system SHALL resolve **trusted reverse-proxy authentication** from YAML (documented key) and `FINOPS_TRUSTED_PROXY_AUTH` (boolean). The system SHALL resolve **IdP group allowlist** from YAML (documented list) and `FINOPS_ALLOWED_IDP_GROUPS` (comma-separated), with env **replacing** YAML for the allowlist when set, consistent with other list env vars. README and `config/settings.yaml` SHALL document all keys and env vars.

#### Scenario: Trusted proxy auth from env overrides YAML

- **WHEN** YAML sets trusted reverse-proxy authentication to false and `FINOPS_TRUSTED_PROXY_AUTH` is set to a **true** value
- **THEN** the resolved value is **true**

#### Scenario: Allowlist from env replaces YAML list

- **WHEN** YAML defines an allowlist and `FINOPS_ALLOWED_IDP_GROUPS` is set
- **THEN** the resolved allowlist is the comma-separated list from the environment only

### Requirement: Resolve LLM provider preference for Bedrock-oriented deployment

The system SHALL resolve an **LLM provider preference** (e.g. `bedrock` vs `openai`) from YAML and `FINOPS_LLM_PROVIDER` such that operators can force **Bedrock** in deployment without relying on absence of an OpenAI key. When unset, existing behavior (infer from presence of OpenAI key vs Bedrock) MAY remain. README and `config/settings.yaml` SHALL document the variable and allowed values.

#### Scenario: FINOPS_LLM_PROVIDER bedrock prefers Bedrock

- **WHEN** `FINOPS_LLM_PROVIDER` is set to **bedrock** (case rules per implementation)
- **THEN** the agent model resolution uses **Bedrock** even if an OpenAI API key is present in the environment
