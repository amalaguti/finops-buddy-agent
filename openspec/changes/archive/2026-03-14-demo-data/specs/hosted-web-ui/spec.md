## ADDED Requirements

### Requirement: Demo route in React router

The web UI SHALL support a `/demo` route that activates demo mode for all child components and API calls.

#### Scenario: /demo route renders app in demo mode

- **WHEN** user navigates to `/demo`
- **THEN** the main application layout renders
- **AND** demo mode context is set to true

#### Scenario: /demo route supports sub-paths

- **WHEN** user navigates to `/demo/mcp_tooling_status`
- **THEN** the tooling status page renders in demo mode

### Requirement: Demo mode header in API calls

When demo mode is active, all API calls from the frontend SHALL include the `X-Demo-Mode: true` header.

#### Scenario: Profile fetch includes demo header

- **WHEN** demo mode is active
- **AND** the frontend fetches `/profiles`
- **THEN** the request includes `X-Demo-Mode: true` header

#### Scenario: Chat request includes demo header

- **WHEN** demo mode is active
- **AND** the frontend sends a chat message
- **THEN** the `/chat` request includes `X-Demo-Mode: true` header

### Requirement: Demo mode badge in header

When demo mode is active, the UI header SHALL display a visible "DEMO" badge to indicate masked data.

#### Scenario: Demo badge visible in header

- **WHEN** demo mode is active
- **THEN** a badge with text "DEMO" is visible in the page header

#### Scenario: Demo badge not visible in normal mode

- **WHEN** demo mode is NOT active
- **THEN** no demo badge is displayed

### Requirement: Profile selector shows masked names

When demo mode is active, the profile selector dropdown SHALL display masked profile names.

#### Scenario: Profile dropdown shows fake names

- **WHEN** demo mode is active
- **AND** the profile selector dropdown is opened
- **THEN** profile names shown are the masked/fake versions from the API response
