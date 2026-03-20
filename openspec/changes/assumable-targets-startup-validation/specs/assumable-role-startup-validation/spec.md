# assumable-role-startup-validation Specification

## Purpose

Validate that **configured FinOps assume-role targets** are **assumable** by the runtime **hub role** before serving traffic (or with explicit warn-only mode), reducing mid-session failures due to **IAM drift**.

## ADDED Requirements

### Requirement: Validation runs when cloud targets are configured

When **cloud deployment mode** is enabled and the **FinOps target map** is non-empty, the system SHALL run a **validation pass** for each configured target role ARN unless explicitly disabled via `FINOPS_*` or YAML. The validation SHALL use **AWS STS** (AssumeRole or documented equivalent) from the **hub** credentials.

#### Scenario: Each target receives a probe

- **WHEN** three targets are configured
- **THEN** the validation pass attempts to validate **all three** (order and concurrency documented)

### Requirement: Strict versus warn-only outcomes

The system SHALL support a **strict** mode where **any** validation failure prevents the API from entering **ready** state (or exits the process), and a **warn** mode where failures are **logged** as errors but the server still starts. The default for **local** development SHALL be **warn** or **disabled** per documented behavior.

#### Scenario: Strict mode fails startup on AccessDenied

- **WHEN** strict validation is enabled and AssumeRole returns AccessDenied for one target
- **THEN** startup fails with a clear message naming the target id and role ARN

### Requirement: Validation does not log temporary credentials

Validation code SHALL **not** write **access key**, **secret**, or **session token** values to logs or audit output.

#### Scenario: Logs show outcome only

- **WHEN** validation runs
- **THEN** logs contain success/failure and error code **only**, not credential material

### Requirement: Configuration documented

`FINOPS_*` keys and YAML options for enable/disable, strict/warn, concurrency, and cooldown SHALL appear in README and `config/settings.yaml`.

#### Scenario: Disable validation in test environments

- **WHEN** validation is disabled via configuration
- **THEN** no STS validation calls are made at startup for targets
