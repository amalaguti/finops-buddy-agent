# backend-api (delta)

## ADDED Requirements

### Requirement: Trusted reverse-proxy authentication gate

When **trusted reverse-proxy authentication** is enabled (via application settings and/or a `FINOPS_*` environment variable documented in README), the HTTP API SHALL reject requests that do not carry **valid authenticated identity context** from the trusted proxy (e.g. **ALB OIDC**-injected headers or documented equivalents). The rejection SHALL use an HTTP **401** or **403** status with a **non-sensitive** message. When trusted reverse-proxy authentication is **disabled**, the backend SHALL **not** require these headers and SHALL retain the existing single-user, CLI-like credential behavior.

#### Scenario: Request without identity is rejected when gate enabled

- **WHEN** trusted reverse-proxy authentication is enabled and a client sends a request to a protected endpoint **without** the expected identity context headers
- **THEN** the response status is **401** or **403** and the body does not include secrets or stack traces intended for internal debugging in production

#### Scenario: Request with identity proceeds when gate enabled

- **WHEN** trusted reverse-proxy authentication is enabled and a client sends a request that includes the **complete** expected identity context from the trusted proxy
- **THEN** the request is processed by the application logic as normal (subject to existing endpoint rules)

#### Scenario: Local dev without proxy still works when gate disabled

- **WHEN** trusted reverse-proxy authentication is disabled and the backend runs locally without ALB
- **THEN** API requests behave as today (no proxy identity headers required)

### Requirement: Optional IdP group allowlist

When a **non-empty** allowlist of IdP groups (or equivalent claim values) is configured (YAML and/or `FINOPS_*` environment variable), the system SHALL parse the authenticated user’s **group** (or configured) claim from the trusted proxy context and SHALL reject the request with **403** if **none** of the allowlisted values are present. When the allowlist is **empty or unset**, the system SHALL **not** perform this check (relying on IdP enterprise app assignment and the authentication gate only).

#### Scenario: User not in allowlisted group is rejected

- **WHEN** trusted reverse-proxy authentication is enabled, the allowlist is non-empty, and the authenticated user’s groups claim does **not** intersect the allowlist
- **THEN** the response status is **403**

#### Scenario: User in allowlisted group is allowed

- **WHEN** trusted reverse-proxy authentication is enabled, the allowlist is non-empty, and the authenticated user’s groups claim **intersects** the allowlist
- **THEN** the request is processed by the application logic as normal

### Requirement: Authenticated subject audit logging

When trusted reverse-proxy authentication is enabled and a request is allowed, the backend SHALL emit a **structured log line** at INFO (or documented level) that includes a **stable user identifier** (e.g. subject or username claim) and **SHALL NOT** log **secrets** (authorization headers, session cookies, raw tokens). The log SHALL be suitable for **session / access auditing** alongside ALB access logs.

#### Scenario: Allowed request logs stable user id

- **WHEN** trusted reverse-proxy authentication is enabled and an allowed request completes successfully
- **THEN** the application logs contain a line associating the request with the **stable user identifier** derived from the proxy identity context

#### Scenario: Logs omit bearer tokens

- **WHEN** trusted reverse-proxy authentication is enabled and logging runs for any request
- **THEN** the application logs do **not** contain the raw **Authorization** header value or complete OIDC **access token** strings
