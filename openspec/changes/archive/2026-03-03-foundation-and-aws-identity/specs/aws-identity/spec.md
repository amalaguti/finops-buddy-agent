# Spec: AWS Identity

## ADDED Requirements

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

The system SHALL be able to list configured AWS profiles from the shared config file (e.g. `~/.aws/config` or path from `AWS_CONFIG_FILE`). Listing SHALL include profile names that can be used for account/role selection. SSO or custom profiles MAY be listed by name even if resolution requires additional steps.

#### Scenario: List profiles from config

- **WHEN** the user requests a list of configured profiles
- **THEN** the system reads the shared config and outputs the list of profile names (excluding the `[default]` section name if present; profile names are typically under `[profile <name>]`)
