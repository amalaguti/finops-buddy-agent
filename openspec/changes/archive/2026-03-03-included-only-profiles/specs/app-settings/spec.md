# app-settings — included-only-profiles (delta)

## ADDED Requirements

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
