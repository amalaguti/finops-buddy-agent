# app-settings Specification (profile-filter-and-app-settings)

## Purpose

Define how the application loads and resolves configuration from a YAML settings file and environment variables, with dotenv support so that `.env` and `.env.local` can supply or override values. Resolved settings (e.g. excluded profiles list) are exposed to the rest of the app.

## ADDED Requirements

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

### Requirement: Load dotenv so .env.local overrides all other sources

The system SHALL load environment variables from `.env` and then from `.env.local` at startup (e.g. at CLI entrypoint). Loading `.env.local` SHALL use `override=True` so that values in `.env.local` override those from `.env` and any pre-existing shell environment. This ensures `.env.local` wins over all other sources for app configuration.

#### Scenario: .env.local overrides .env

- **WHEN** both `.env` and `.env.local` exist and define the same variable (e.g. `FINOPS_EXCLUDED_PROFILES`)
- **THEN** the value from `.env.local` is used after dotenv load

#### Scenario: Missing .env or .env.local does not error

- **WHEN** `.env` or `.env.local` is missing
- **THEN** the system loads the existing file(s) only; missing files SHALL NOT cause the app to fail
