# typed-application-settings Specification

## Purpose

Replace ad-hoc settings getters with a **validated, typed** configuration object suitable for **multi-user cloud** deployments and growing `FINOPS_*` surface area.

## ADDED Requirements

### Requirement: Single validated settings object

The system SHALL expose a **single** application settings object (or frozen snapshot) constructed at startup (or first access with explicit cache) that contains **all** user-configurable fields required by core modules. The object SHALL be produced using a **schema-validated** mechanism (e.g. Pydantic) such that **type errors** and **constraint violations** are detected when the object is built.

#### Scenario: Invalid integer env var rejected at load

- **WHEN** a `FINOPS_*` variable expected to be a positive integer is set to a non-numeric value
- **THEN** settings construction fails with a clear validation error (or strict-mode behavior per configuration)

### Requirement: Precedence matches existing project rules

Resolved values SHALL follow **documented precedence** consistent with `app-settings`: in particular, **environment variables** SHALL override YAML for keys where the existing specification states env replaces YAML. New behavior SHALL NOT silently change precedence for existing keys without a **BREAKING** note in the change proposal.

#### Scenario: Env still overrides YAML for excluded profiles list

- **WHEN** YAML defines `excluded_profiles` and `FINOPS_EXCLUDED_PROFILES` is set
- **THEN** the resolved excluded list matches the **environment** value after refactor, same as before

### Requirement: Optional strict startup mode

The system SHALL support a documented **strict** settings mode (via `FINOPS_*` or YAML) that **fails application startup** when validation errors occur, recommended for **production** deployments.

#### Scenario: Production strict mode exits on bad config

- **WHEN** strict mode is enabled and a required production field is missing
- **THEN** the process exits during startup with a non-zero status and a clear message

### Requirement: Dependency and documentation

Adding the typed settings implementation SHALL declare any new Python dependency in **`pyproject.toml`** (e.g. `pydantic-settings`). README and `config/settings.yaml` SHALL be updated to describe **nested keys**, **env aliases**, and **strict** mode.

#### Scenario: Poetry lock updated

- **WHEN** the change is merged
- **THEN** `pyproject.toml` / lockfile reflect the new dependency version constraints
