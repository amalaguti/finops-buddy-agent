## ADDED Requirements

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

Demo mode account mappings SHALL be configurable via the settings file under `demo.account_mapping`.

#### Scenario: Custom mapping in settings

- **WHEN** settings YAML contains `demo.account_mapping` with entries
- **THEN** those mappings are used for demo mode masking

#### Scenario: Default behavior without configuration

- **WHEN** no `demo.account_mapping` is configured
- **THEN** all accounts use auto-generated fake names
