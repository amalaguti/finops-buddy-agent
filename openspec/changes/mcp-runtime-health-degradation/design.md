## Context

FinOps Buddy is **read-only**; degradation should **fail safe** (no partial writes). User trust requires **clear** “Billing MCP unavailable” style messages.

## Goals / Non-Goals

**Goals:** Bounded wait times; breaker trips after repeated failures; operator-visible reasons in logs (no secrets).

**Non-Goals:** Auto-restart MCP processes in this change (optional follow-up); remote MCP over TCP.

## Decisions

| Decision | Rationale |
|----------|-----------|
| Timeout on each tool call into MCP | Prevents hung chat. |
| Breaker per server name | Isolates failures. |
| User-visible degradation string | Meets supportability goals. |

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| False positives (slow cold start) | Longer threshold for first call after warm-up; align with MCP loading phases. |

## Migration Plan

Defaults preserve current behavior until `FINOPS_MCP_*` resilience flags are enabled.

## Open Questions

- Interaction with **agent warm-up** (pre-flight health vs lazy).
