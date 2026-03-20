# aws-identity (delta)

## ADDED Requirements

### Requirement: Cloud deployment mode uses the default AWS credential chain

When **cloud deployment mode** is enabled (via application settings and/or a `FINOPS_*` environment variable documented in README), the system SHALL obtain **base** AWS credentials using the **default boto3 credential chain** (environment variables, **ECS/EC2 instance metadata** for task/instance roles, etc.) and SHALL **not** require a `~/.aws` directory to be present for that base session. When cloud deployment mode is **not** enabled, existing behavior (CLI config and profiles) SHALL remain unchanged.

#### Scenario: Cloud mode uses default chain when no profile file exists

- **WHEN** cloud deployment mode is enabled and the process runs in an environment where the **only** credentials are provided by the **ECS task role** (no shared config file)
- **THEN** the system successfully creates an AWS session using the task role credentials for **base** API calls that do not require a specific member-account role

#### Scenario: Local mode unchanged when cloud mode disabled

- **WHEN** cloud deployment mode is disabled and a named profile exists in the shared config
- **THEN** the system continues to resolve sessions using **profile-based** configuration as specified in the existing aws-identity specification

### Requirement: Configurable FinOps target map for AssumeRole

When cloud deployment mode is enabled and a **FinOps target map** is configured (YAML and/or `FINOPS_*` environment variables as documented), the system SHALL expose a list of **selectable targets** (each with a stable identifier, e.g. account id or logical label) and SHALL resolve each target to a **role ARN** (or structured assume-role request) that the base session **SHALL** assume via **STS AssumeRole** before executing account-scoped FinOps calls for that target. When no map is configured, the system SHALL behave according to documented defaults (e.g. single-account using only the base session, or clear error if multi-account listing is requested).

#### Scenario: Resolve credentials for a mapped target

- **WHEN** cloud deployment mode is enabled and the FinOps target map contains an entry mapping **target T** to **role ARN R**, and the user or API selects **T**
- **THEN** the system calls **STS AssumeRole** (or equivalent) to obtain credentials for **R** before performing Cost Explorer (or other account-scoped) operations for **T**

#### Scenario: Unknown target is rejected

- **WHEN** cloud deployment mode is enabled and the client selects a target identifier that is not present in the FinOps target map
- **THEN** the system returns a clear error and does not invoke AWS APIs with a guessed role
