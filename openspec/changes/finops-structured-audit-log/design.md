## Context

Align with **ALB access logs** (network) + **app audit** (data). Fields should map cleanly to **SIEM** parsers.

## Goals / Non-Goals

**Goals:** Stable **event type** enum; **actor** (sub), **resource** (account id / target id), **action**, **result**; redaction defaults.

**Non-Goals:** Long-term storage implementation in AWS in v1 (can be phase 2).

## Decisions

| Field | Example |
|-------|---------|
| `event_type` | `finops.costs.read`, `finops.chat.tool_call` |
| `actor_sub` | from ALB-injected header |
| `target_account_id` | resolved from session/role |
| `tool_name` | MCP or built-in tool id |

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Log volume | Sample or rate-limit debug-only fields. |
| PII in prompts | Default omit; configurable max length hash-only. |

## Migration Plan

Behind `FINOPS_AUDIT_LOG_ENABLED`; default **on** when trusted proxy auth on (or explicit opt-in — decide in tasks).

## Open Questions

- Corporate retention **365d** requirement vs cost.
