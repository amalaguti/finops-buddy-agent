# Spec: Master/Payer Context

## ADDED Requirements

### Requirement: Identify current account context

The system SHALL be able to report which AWS account is currently in use (from the resolved identity). The system SHALL support an optional configuration or environment variable to designate the “Master/Payer” account ID (or profile name) so that the CLI can indicate whether the current account is the master/payer or a linked account.

#### Scenario: Current account is reported

- **WHEN** the user requests account context (e.g. as part of identity or a dedicated command)
- **THEN** the system outputs the current account ID and, if configured, whether it is considered the Master/Payer account

#### Scenario: Master/Payer is configured

- **WHEN** the user (or deployment) sets a config value or env var for the Master/Payer account ID (e.g. `FINOPS_MASTER_ACCOUNT_ID` or a key in a config file)
- **THEN** the system uses that value to compare with the current account ID and reports “master/payer” or “linked” (or equivalent) when reporting context

### Requirement: Placeholder when Master/Payer not configured

If no Master/Payer account is configured, the system SHALL still report the current account ID and SHALL report Master/Payer status as “unknown” or omit it, without failing. The system SHALL NOT require AWS Organizations API for this change.

#### Scenario: No Master/Payer config

- **WHEN** no Master/Payer account ID (or profile) is configured and the user requests account context
- **THEN** the system outputs the current account ID and does not assert master vs linked (or displays “unknown”)
