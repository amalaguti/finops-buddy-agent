# aws-identity Specification

## Purpose
TBD - created by archiving change foundation-and-aws-identity. Update Purpose after archive.
## Requirements
### Requirement: Use existing AWS CLI config

The CLI SHALL use the existing AWS CLI configuration for credentials and region (environment variables, shared credentials file, shared config file, or default profile). The system SHALL NOT introduce new credential mechanisms; it SHALL rely on the default credential chain (e.g. boto3 default session).

#### Scenario: Default credentials are used when no profile specified

- **WHEN** the user runs the CLI without specifying a profile (and no env overrides)
- **THEN** the system uses the default credential chain (e.g. default profile or env vars) to create an AWS session

#### Scenario: Named profile is used when specified

- **WHEN** the user specifies a profile (e.g. via `--profile` or `AWS_PROFILE`)
- **THEN** the system uses that profile from the shared config for the session

### Requirement: Resolve current identity

The system SHALL be able to resolve and display the current AWS identity (account ID, user/role ARN) for the active session. This SHALL use AWS STS GetCallerIdentity (or equivalent) with the resolved session.

#### Scenario: Current identity is displayed

- **WHEN** the user requests current identity (e.g. via a “whoami” or “identity” command)
- **THEN** the system outputs the account ID and principal (user or role ARN) for the active credentials

### Requirement: List configured profiles

The system SHALL be able to list configured AWS profiles from the shared config file (e.g. `~/.aws/config` or path from `AWS_CONFIG_FILE`). When the app's resolved **included_only_profiles** list is **non-empty**, listing SHALL return only profile names that appear in that list and in the shared config (intersection); any other profile is considered out of scope. When the included_only_profiles list is **empty or absent**, listing SHALL include only profile names that are **not** in the app's resolved excluded-profiles list (from app settings). Profile names returned SHALL be those that can be used for account/role selection. SSO or custom profiles MAY be listed by name even if resolution requires additional steps. The excluded list SHALL be obtained from the app settings module (YAML defaults and/or `FINOPS_EXCLUDED_PROFILES`); when the excluded list is empty and included_only is empty, all configured profiles SHALL be returned.

#### Scenario: List profiles from config excluding configured names

- **WHEN** the user requests a list of configured profiles and app settings define an excluded-profiles list and included_only_profiles is empty
- **THEN** the system reads the shared config and outputs only profile names that are not in the excluded list (excluding the `[default]` section name if present; profile names are typically under `[profile <name>]`)

#### Scenario: List all profiles when no exclusions are configured

- **WHEN** the user requests a list of configured profiles and the resolved excluded-profiles list is empty and included_only_profiles is empty
- **THEN** the system reads the shared config and outputs the full list of profile names (excluding the `[default]` section name if present)

#### Scenario: List only included profiles when allowlist is set

- **WHEN** the user requests a list of configured profiles and the resolved included_only_profiles list is non-empty
- **THEN** the system reads the shared config and outputs only profile names that are in the included_only_profiles list (intersection of config profiles and included list); profiles not in the list are omitted

#### Scenario: Allowlist takes precedence over blocklist

- **WHEN** both included_only_profiles and excluded_profiles are configured and included_only_profiles is non-empty
- **THEN** the system uses only the included_only list for filtering; the excluded list is ignored for profile listing

