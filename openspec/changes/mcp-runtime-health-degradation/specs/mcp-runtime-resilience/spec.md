# mcp-runtime-resilience Specification

## Purpose

Define **timeouts, health checks, and circuit breaking** for MCP subprocess clients so chat does not hang silently when an MCP server crashes or stalls.

## ADDED Requirements

### Requirement: Tool calls to MCP servers use a bounded timeout

The system SHALL enforce a **configurable maximum wall-clock time** for MCP tool invocations (per server or global default via `FINOPS_*` / settings). When exceeded, the call SHALL fail with a **catchable error** classified as **timeout** and SHALL NOT block the event loop indefinitely.

#### Scenario: Slow MCP exceeds timeout

- **WHEN** an MCP tool call exceeds the configured timeout
- **THEN** the call fails with a timeout classification and the agent receives an error suitable for user-facing degradation messaging

### Requirement: Circuit breaker for repeated MCP failures

The system SHALL track **consecutive failures** per MCP server (or client id) and enter an **open** state that **fast-fails** further calls for a **cooldown period** after a **documented threshold** is reached. After cooldown, a **half-open** trial MAY be allowed.

#### Scenario: Open circuit fast-fails without spawning new subprocess storm

- **WHEN** the circuit for MCP server M is open
- **THEN** subsequent tool calls to M fail immediately without starting unbounded new subprocess attempts

### Requirement: User-visible degraded behavior

When an MCP server is unavailable (timeout, open circuit, or process exit), the system SHALL include in the chat outcome a **clear message** identifying which capability is degraded (e.g. “Billing MCP unavailable”). The system SHALL NOT claim successful tool results for that server.

#### Scenario: Chat continues with remaining tools

- **WHEN** one MCP is unavailable but others remain healthy
- **THEN** the agent can still proceed with non-dependent tools and the user sees which MCP failed

### Requirement: Configurable resilience parameters

Resilience behavior SHALL be configurable via **YAML** and **`FINOPS_`-prefixed** environment variables (timeouts, failure thresholds, cooldown). README and `config/settings.yaml` SHALL document keys.

#### Scenario: Environment overrides YAML for MCP timeout

- **WHEN** both YAML and `FINOPS_MCP_TOOL_TIMEOUT_SECONDS` (or documented equivalent) are set
- **THEN** the environment value wins per project precedence rules
