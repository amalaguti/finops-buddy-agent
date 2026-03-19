## ADDED Requirements

### Requirement: costs subcommand accepts --profile after subcommand name

The `costs` subcommand SHALL accept the optional `--profile` (and `-p`) argument so that the AWS profile can be specified either before or after the subcommand name. Behavior and output SHALL be unchanged regardless of argument order.

#### Scenario: profile before subcommand

- **WHEN** the user runs `finops --profile payer-profile costs`
- **THEN** the CLI runs costs for the AWS profile `payer-profile` and exits with code 0 (or non-zero only on cost/credential errors)

#### Scenario: profile after subcommand

- **WHEN** the user runs `finops costs --profile payer-profile`
- **THEN** the CLI runs costs for the AWS profile `payer-profile` and exits with code 0 (or non-zero only on cost/credential errors)

#### Scenario: no profile uses default

- **WHEN** the user runs `finops costs` without `--profile`
- **THEN** the CLI runs costs using the default profile (e.g. AWS_PROFILE or default) and exits as above
