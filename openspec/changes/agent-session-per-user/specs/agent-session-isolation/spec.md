# agent-session-isolation Specification

## Purpose

Define **isolated agent and tool runtime scopes** so multi-user cloud deployments do not leak chat context or MCP/agent singleton state between users.

## ADDED Requirements

### Requirement: Resolve a stable session key per HTTP chat request

The system SHALL resolve a **session key** for chat and agent-scoped operations. When **trusted reverse-proxy authentication** is enabled (per `deploy-aws` / `backend-api` settings), the session key SHALL be derived from **authenticated identity claims** (e.g. subject and issuer) supplied by the trusted proxy. When trusted authentication is disabled, the system SHALL use a **single process-default** session key so local single-user behavior is unchanged unless explicitly configured otherwise.

#### Scenario: Distinct keys for two authenticated users

- **WHEN** two concurrent chat requests include different authenticated subject values from the trusted proxy
- **THEN** the system uses **different** session keys for agent resolution for each request

#### Scenario: Single default key locally

- **WHEN** trusted reverse-proxy authentication is disabled and no optional per-user override is configured
- **THEN** all chat requests in that process share the **same** default session key

### Requirement: No shared mutable agent conversation state across session keys

The system SHALL NOT reuse the same **in-memory agent instance**, **conversation state**, or **MCP client pool** across **different** session keys for chat handling. Shared **read-only** configuration (settings schema, static prompts) MAY be reused.

#### Scenario: Concurrent chats do not cross session boundaries

- **WHEN** session key A and session key B each have an active chat stream
- **THEN** messages and tool results for A are not visible to B’s agent state

### Requirement: Bounded session registry

The system SHALL enforce an upper bound on the number of **concurrent session keys** holding agent-related state (LRU eviction, TTL, or equivalent) and SHALL document the `FINOPS_*` or settings keys controlling bounds.

#### Scenario: Eviction under pressure

- **WHEN** the number of distinct session keys exceeds the configured maximum
- **THEN** the system evicts or refuses new sessions per documented policy without crashing the process
