## ADDED Requirements

### Requirement: Demo mode middleware

The backend API SHALL include middleware that detects the `X-Demo-Mode: true` request header and transforms responses to mask sensitive identifiers.

#### Scenario: Middleware masks profile list response

- **WHEN** a request to `/profiles` includes `X-Demo-Mode: true` header
- **THEN** the response profile names are replaced with fake names

#### Scenario: Middleware masks context response

- **WHEN** a request to `/context` includes `X-Demo-Mode: true` header
- **THEN** account name and account ID in the response are masked

#### Scenario: Middleware masks costs response

- **WHEN** a request to `/costs` includes `X-Demo-Mode: true` header
- **THEN** any account identifiers in the response are masked

#### Scenario: Non-demo requests are unchanged

- **WHEN** a request does NOT include `X-Demo-Mode: true` header
- **THEN** the response is returned unmodified

### Requirement: Demo mode chat system prompt

When demo mode is active for a chat request, the agent's system prompt SHALL include instructions to use fake account names and IDs in responses.

#### Scenario: Chat request with demo mode

- **WHEN** a `/chat` request includes `X-Demo-Mode: true` header
- **THEN** the agent system prompt includes demo mode masking instructions
- **AND** the agent uses fake names in its streamed response

#### Scenario: Demo masking instructions include configured mapping

- **WHEN** demo mode is active
- **AND** settings contain `demo.account_mapping` entries
- **THEN** the masking instructions include those specific mappings
