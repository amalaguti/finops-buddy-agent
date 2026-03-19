# aws-identity Specification (profile-filter-and-app-settings delta)

## Purpose

Delta spec for profile-filter-and-app-settings: list configured profiles SHALL respect the excluded-profiles list from app settings.

## MODIFIED Requirements

### Requirement: List configured profiles

The system SHALL be able to list configured AWS profiles from the shared config file (e.g. `~/.aws/config` or path from `AWS_CONFIG_FILE`). Listing SHALL include only profile names that are **not** in the app's resolved excluded-profiles list (from app settings). Profile names returned SHALL be those that can be used for account/role selection. SSO or custom profiles MAY be listed by name even if resolution requires additional steps. The excluded list SHALL be obtained from the app settings module (YAML defaults and/or `FINOPS_EXCLUDED_PROFILES`); when the excluded list is empty, all configured profiles SHALL be returned.

#### Scenario: List profiles from config excluding configured names

- **WHEN** the user requests a list of configured profiles and app settings define an excluded-profiles list
- **THEN** the system reads the shared config and outputs only profile names that are not in the excluded list (excluding the `[default]` section name if present; profile names are typically under `[profile <name>]`)

#### Scenario: List all profiles when no exclusions are configured

- **WHEN** the user requests a list of configured profiles and the resolved excluded-profiles list is empty
- **THEN** the system reads the shared config and outputs the full list of profile names (excluding the `[default]` section name if present)
