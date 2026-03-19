# backend-api Specification

## Purpose

Defines the HTTP API layer for the FinOps Agent: read-only endpoints (profiles, context, costs) and chat with streaming, in single-user mode, reusing the CLI's profile and credential model.

## ADDED Requirements

### Requirement: HTTP API lists profiles

The system SHALL expose an HTTP endpoint that returns the list of configured AWS profile names. The list SHALL be filtered using the same rules as the CLI: when the app's resolved included_only_profiles list is non-empty, only profiles in that list SHALL be returned; otherwise, profiles in the excluded_profiles list SHALL be omitted. The endpoint SHALL use the same app settings and FINOPS_ environment variables as the CLI for profile filtering.

#### Scenario: GET profiles returns filtered list

- **WHEN** a client sends a GET request to the profiles endpoint and app settings define an excluded-profiles list (and included_only is empty)
- **THEN** the response body contains a list of profile names that are not in the excluded list, and the response status is 200

#### Scenario: GET profiles with included_only_profiles

- **WHEN** a client sends a GET request to the profiles endpoint and the resolved included_only_profiles list is non-empty
- **THEN** the response body contains only profile names that are in the included_only list (intersection with shared config), and the response status is 200

### Requirement: HTTP API returns account context

The system SHALL expose an HTTP endpoint that returns the current account context (account ID, ARN, role, and master/payer indication) for a given or default AWS profile. The profile SHALL be specified via an optional query parameter or header (e.g. `profile` or `X-AWS-Profile`). When not specified, the system SHALL use the same default as the CLI (e.g. `AWS_PROFILE` from the environment or first available profile). The endpoint SHALL use the same core logic as the CLI context command.

#### Scenario: GET context returns account info for default profile

- **WHEN** a client sends a GET request to the context endpoint without a profile parameter and the backend has a valid default profile
- **THEN** the response body contains account_id, arn, role, and master/payer information and the response status is 200

#### Scenario: GET context with profile parameter

- **WHEN** a client sends a GET request to the context endpoint with a valid profile query parameter
- **THEN** the response body contains account context for that profile and the response status is 200

#### Scenario: GET context fails when credentials invalid

- **WHEN** a client sends a GET request to the context endpoint and the resolved profile has invalid or missing credentials
- **THEN** the response status is an error (4xx or 5xx) and the response body includes a clear error message

### Requirement: HTTP API returns current-month costs by service

The system SHALL expose an HTTP endpoint that returns current-month costs grouped by AWS service for a given or default profile. The profile SHALL be specified via an optional query parameter or header, consistent with the context endpoint. The response SHALL contain a list of service names and cost amounts (e.g. in the account currency). The endpoint SHALL use the same core logic as the CLI costs command (Cost Explorer GetCostAndUsage or equivalent).

#### Scenario: GET costs returns cost data for profile

- **WHEN** a client sends a GET request to the costs endpoint with a valid profile (or default)
- **THEN** the response body contains a list of service and cost entries for the current month and the response status is 200

#### Scenario: GET costs fails when Cost Explorer access denied

- **WHEN** a client sends a GET request to the costs endpoint and the resolved session does not have Cost Explorer permissions (or API returns an error)
- **THEN** the response status is an error (4xx or 5xx) and the response body includes a clear error message

### Requirement: HTTP API provides chat with streaming response

The system SHALL expose an HTTP endpoint (or channel) for chat that accepts a user message and optional conversation history and returns the agent's response as a stream (e.g. Server-Sent Events or chunked transfer). The client SHALL receive response content incrementally (chunks or tokens) so that the UI can display progress. The endpoint SHALL use the same Strands agent and tooling as the CLI chat; profile SHALL be selectable via optional parameter or header. The system MAY accept a list of prior messages in the request body to support multi-turn conversation with a stateless server.

#### Scenario: POST chat streams agent response

- **WHEN** a client sends a POST request to the chat endpoint with a message body and accepts a streaming response type (e.g. text/event-stream)
- **THEN** the server responds with a stream (e.g. SSE) and the client receives one or more events containing the agent's reply (or chunks of it), and the response status is 200

#### Scenario: Chat respects read-only guardrails

- **WHEN** a client sends a message that is detected as mutating intent (e.g. create, delete) and the read-only input guardrail is enabled
- **THEN** the streamed response (or final response) contains the same friendly read-only message as the CLI and no tool calls are executed for that request

### Requirement: Backend single-user and CLI-like credentials

The backend SHALL operate in single-user mode: no per-user authentication or tenant isolation. Credentials and profile selection SHALL be managed in a similar fashion to the CLI: the backend process SHALL use the same credential chain (environment variables, shared config, settings file). Profile selection for endpoints SHALL be via optional query parameter or header; when absent, the default profile (e.g. from AWS_PROFILE) SHALL be used. All FINOPS_ and AWS_ environment variables used by the CLI SHALL apply to the backend when serving requests.

#### Scenario: Backend uses AWS_PROFILE for default profile

- **WHEN** the backend process has AWS_PROFILE set and a request to an endpoint that requires a profile does not include a profile parameter
- **THEN** the backend uses that profile to resolve the session and execute the request

#### Scenario: Request can override profile

- **WHEN** a client sends a request with a profile query parameter or header (e.g. profile=my-profile)
- **THEN** the backend uses that profile for that request (subject to the same config as the CLI, e.g. excluded/included lists)

### Requirement: Backend configuration

The system SHALL support backend-specific configuration for the HTTP server (e.g. host, port, CORS origins) via the application settings file and environment variables. All new environment variables SHALL use the FINOPS_ prefix. The settings file (and optional backend section) and env vars SHALL be documented in the README; the config/settings.yaml template SHALL include the new keys (commented or with placeholders). Precedence SHALL match the CLI: environment variables override the settings file.

#### Scenario: Server listens on configured host and port

- **WHEN** the backend is started and the settings file (or env) specifies a host and port (e.g. FINOPS_SERVER_PORT=9000)
- **THEN** the HTTP server binds to that host and port and accepts requests there

#### Scenario: Default bind when no server config

- **WHEN** the backend is started and no server host/port is configured
- **THEN** the server uses a safe default (e.g. 127.0.0.1 and a default port) so it is not exposed to the network by default
