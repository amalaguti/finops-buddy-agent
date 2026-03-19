# Spec: Verify AWS credentials

## ADDED Requirements

### Requirement: Library verifies credentials for profile or default

The system SHALL provide a function that verifies AWS credentials for the default credential chain or a given profile name. The function SHALL call STS GetCallerIdentity and return the resolved identity (account ID, ARN, user ID). When an expected account ID is provided, the function SHALL raise a dedicated exception if the resolved account does not match.

#### Scenario: Verify with profile returns identity

- **WHEN** the caller invokes the verify function with a profile name and credentials for that profile are valid
- **THEN** the function returns the CurrentIdentity (account_id, arn, user_id) and does not raise

#### Scenario: Verify with expected account ID matching

- **WHEN** the caller invokes the verify function with expected_account_id equal to the resolved account ID
- **THEN** the function returns the CurrentIdentity and does not raise

#### Scenario: Verify with expected account ID mismatch

- **WHEN** the caller invokes the verify function with expected_account_id different from the resolved account ID
- **THEN** the function raises WrongAccountError with expected and actual account ID

### Requirement: CLI verify command

The CLI SHALL provide a `verify` subcommand that verifies AWS credentials for the current or specified profile. The command SHALL accept the same profile selection as other commands (e.g. `--profile` before or after the subcommand). The command SHALL optionally accept `--account-id` to require the credentials to resolve to that account ID. On success the command SHALL print OK with account ID and ARN and exit 0; on wrong account or other errors it SHALL print a clear error to stderr and exit 1.

#### Scenario: Verify default profile

- **WHEN** the user runs `finops verify` with no profile specified
- **THEN** the CLI uses the default credential chain (AWS_PROFILE or default profile), calls STS, and prints OK with account ID and ARN on success

#### Scenario: Verify with profile after subcommand

- **WHEN** the user runs `finops verify --profile my-prod`
- **THEN** the CLI uses profile my-prod for the verification and prints OK or error accordingly

#### Scenario: Verify with profile before subcommand

- **WHEN** the user runs `finops --profile my-prod verify`
- **THEN** the CLI uses profile my-prod for the verification and prints OK or error accordingly

#### Scenario: Verify with required account ID

- **WHEN** the user runs `finops verify --profile my-prod --account-id 123456789012` and the credentials resolve to that account
- **THEN** the CLI prints OK and exits 0

#### Scenario: Wrong account exits with error

- **WHEN** the user runs `finops verify --account-id 111111111111` and the credentials resolve to a different account
- **THEN** the CLI prints an error indicating wrong account (expected vs actual) to stderr and exits 1
