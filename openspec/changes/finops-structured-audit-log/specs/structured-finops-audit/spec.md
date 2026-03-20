# structured-finops-audit Specification

## Purpose

Define **structured audit events** for sensitive FinOps operations in **multi-user cloud** deployments, beyond generic HTTP access logs.

## ADDED Requirements

### Requirement: Structured audit record schema

The system SHALL emit audit records as **structured data** (JSON object per line on stdout or documented sink) containing at minimum: **timestamp** (ISO 8601), **event_type** (stable string enum), **result** (`success` / `denied` / `error`), and **request_correlation_id** when available. When trusted reverse-proxy authentication is enabled, records SHALL include **actor_subject** (or documented stable id field) derived from proxy headers.

#### Scenario: Costs read produces finops audit event

- **WHEN** an authenticated user successfully fetches cost data for a resolved AWS target
- **THEN** the system emits one audit record with `event_type` identifying cost read and includes the **target identifier** (account id or configured target id) and **result** success

### Requirement: Chat tool invocations audited at tool boundary

When the agent invokes a **tool** (MCP or built-in), the system SHALL emit an audit record including **tool name**, **session or user key** (hashed or id per privacy policy), **target account** if applicable, and **result** status. The record SHALL **not** include the **full user prompt** or **full model output** unless a **explicit** `FINOPS_AUDIT_LOG_INCLUDE_CONTENT` (or documented) flag is enabled (default **off**).

#### Scenario: Tool call audit omits prompt by default

- **WHEN** a tool is invoked during chat and content logging is disabled
- **THEN** the audit record contains tool name and outcome but **does not** contain the raw user message body

### Requirement: No secrets in audit stream

Audit emission code SHALL **not** write **Authorization** headers, **session cookies**, **OIDC access tokens**, or **AWS temporary credentials** to audit output.

#### Scenario: Token never appears in audit line

- **WHEN** any request includes a bearer token or cookie
- **THEN** no audit record field contains the literal secret value

### Requirement: Configuration and documentation

Audit behavior SHALL be configurable via **`FINOPS_*`** and YAML (enable/disable, optional sink, optional content inclusion). README and `config/settings.yaml` SHALL document fields and **privacy** implications.

#### Scenario: Audit disabled for local dev

- **WHEN** audit is disabled via configuration
- **THEN** no finops audit records are emitted (HTTP server logs may still exist separately)
