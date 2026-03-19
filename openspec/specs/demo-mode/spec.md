# Demo Mode

Demo mode masks real AWS account names, profile names, and account IDs with fake values for presentations.

## Requirements

### Requirement: Demo mode activation via URL

The web UI SHALL support a `/demo` URL path that activates demo mode. When demo mode is active, all sensitive AWS identifiers (account names, profile names, account IDs) SHALL be masked with fake values throughout the UI and in chat responses.

#### Scenario: User navigates to /demo

- **WHEN** a user navigates to `/demo` in the browser
- **THEN** the web UI loads in demo mode
- **AND** all API calls include `X-Demo-Mode: true` header

#### Scenario: Demo mode is URL-based only

- **WHEN** a user navigates to `/` (root path)
- **THEN** demo mode is NOT active
- **AND** real account names and IDs are displayed

### Requirement: Account name masking

When demo mode is active, account names and profile names SHALL be replaced with configured or auto-generated fake names. The mapping SHALL be configurable via settings.

#### Scenario: Configured account mapping applies

- **WHEN** demo mode is active
- **AND** an account name matches a configured mapping (e.g., `payer-profile` → `Master_Account`)
- **THEN** the configured fake name is displayed instead of the real name

#### Scenario: Unmapped accounts get auto-generated names

- **WHEN** demo mode is active
- **AND** an account name has no configured mapping
- **THEN** a generated fake name is used (e.g., `Account_001`, `Account_002`)

#### Scenario: Profile names are masked

- **WHEN** demo mode is active
- **THEN** AWS profile names in the profile selector are replaced with fake names

### Requirement: Account ID masking

When demo mode is active, AWS account IDs (12-digit numbers) SHALL be replaced with fake IDs.

#### Scenario: Account IDs are masked

- **WHEN** demo mode is active
- **AND** an API response contains an AWS account ID
- **THEN** the account ID is replaced with a fake 12-digit ID (e.g., `000000000001`)

### Requirement: Chat response masking

When demo mode is active, the chat agent SHALL use fake names in its responses instead of real account names and IDs.

#### Scenario: Agent uses fake names in responses

- **WHEN** demo mode is active
- **AND** the user asks about costs for an account
- **THEN** the agent's response uses the mapped fake name instead of the real account name

#### Scenario: Agent masks account IDs in responses

- **WHEN** demo mode is active
- **AND** the agent would mention an account ID
- **THEN** the agent uses a masked or fake ID instead

### Requirement: Demo mode visual indicator

When demo mode is active, the UI SHALL display a visible indicator so users know they are viewing masked data.

#### Scenario: Demo badge is visible

- **WHEN** demo mode is active
- **THEN** a "DEMO" badge or indicator is visible in the UI header

### Requirement: Demo mode configuration

Demo mode account mappings SHALL be configurable via `config/demo.yaml`, auto-generated from AWS config.

#### Scenario: Generate demo config from AWS profiles

- **WHEN** user runs `finops demo-config`
- **THEN** `config/demo.yaml` is generated from `~/.aws/config`
- **AND** account names are mapped to city-based fake names
- **AND** account IDs are mapped to random 12-digit numbers

#### Scenario: Demo config is gitignored

- **WHEN** `config/demo.yaml` is generated
- **THEN** the file is excluded from git commits (via .gitignore)

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
