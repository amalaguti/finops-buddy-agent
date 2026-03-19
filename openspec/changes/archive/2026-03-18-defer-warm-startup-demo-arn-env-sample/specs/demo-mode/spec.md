# demo-mode (delta): ARN session name masking

## ADDED Requirements

### Requirement: ARN session name masked in account context

When demo mode is active, the account context response SHALL mask the ARN string by replacing the assumed-role session name (the part after the last `/` in ARNs of the form `...assumed-role/RoleName/session-name`) with a fixed placeholder (e.g. `john.doe@finops.buddy`). Account IDs within the ARN SHALL continue to be masked per existing account ID masking. This prevents the account details pane (e.g. on `/demo`) from exposing real session identifiers or PII such as email addresses.

#### Scenario: Assumed-role ARN session name is replaced

- **WHEN** a request to `/context` includes `X-Demo-Mode: true` header
- **AND** the resolved context has an ARN containing `assumed-role` and a session name (e.g. `arn:aws:sts::123456789012:assumed-role/MyRole/user@example.com`)
- **THEN** the response `arn` field has the account ID masked (per existing rules)
- **AND** the segment after the last `/` in the assumed-role part is replaced with the configured placeholder (e.g. `john.doe@finops.buddy`)

#### Scenario: Account details pane shows no real email in demo

- **WHEN** a user views the account details pane in the UI under `/demo`
- **THEN** the displayed ARN does not contain the real assumed-role session name (e.g. email)
- **AND** a placeholder value is shown instead
