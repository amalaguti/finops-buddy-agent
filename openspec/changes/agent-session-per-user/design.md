## Context

Multi-user internal deployment (see `deploy-aws`, OIDC) requires **logical isolation** of agent state. Today, efficiency favors one warmed process; cloud favors **correctness under concurrency**.

## Goals / Non-Goals

**Goals:** Per-user (or per-session-id) **agent and tool context**; clear eviction/TTL policy; load test showing two users do not see each other’s streams.

**Non-Goals:** Full chat history persistence in Redis/DB in this change (optional follow-up); horizontal session affinity beyond what ALB already provides.

## Decisions

| Decision | Rationale |
|----------|-----------|
| Session key = OIDC `sub` (+ issuer) when trusted auth on | Stable, no PII in key; composite if needed for tenant split. |
| Fallback session for local single-user | Preserves current DX. |
| LRU or TTL cap on sessions | Prevents memory exhaustion on Fargate. |

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Memory per session | TTL + max sessions + metrics. |
| Warm-up cost per session | Lazy warm on first chat; shared read-only config caches where safe. |

## Migration Plan

Feature-flag optional (`FINOPS_PER_USER_AGENT_SESSIONS`); default **on** when `FINOPS_TRUSTED_PROXY_AUTH` is on; default **off** for local.

## Open Questions

- Whether to support explicit `X-Session-Id` for anonymous multi-tab continuity.
- Interaction with SSE stickiness (see `chat-sse-websocket-resilience`).
