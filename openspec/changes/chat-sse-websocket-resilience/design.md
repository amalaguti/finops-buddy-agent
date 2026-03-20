## Context

ALB supports **WebSockets**; SSE works but is **one-way** and **HTTP/1.1**-oriented. Sticky cookies **do not survive** task replacement gracefully without client retry.

## Goals / Non-Goals

**Goals:** Define a **reconnect strategy**; prefer standards (`Last-Event-ID` where feasible); document **limitations** if full resume is impossible (e.g. MCP already ran).

**Non-Goals:** Guaranteed exactly-once tool side effects across reconnect (read-only tool stance limits risk; still document).

## Decisions

| Option | Notes |
|--------|------|
| A: SSE + reconnect + best-effort resume | Smaller change; may only replay **assistant text** buffer. |
| B: WebSocket for cloud only | Cleaner bidirectional; more server complexity. |
| C: Both | Feature-flag transport. |

**Recommendation (open):** prototype **SSE reconnect** first; add **WS** if product requires mid-stream cancellation or binary frames.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Duplicate tool calls on resume | Idempotency keys or “resume read-only” mode. |
| Buffer memory | Cap replay buffer size per stream. |

## Migration Plan

Ship client reconnect behind feature flag; server advertises `supports_resume: false` until implemented.

## Open Questions

- Whether **EventSource** polyfill needs custom headers for auth (cookies vs bearer) behind ALB OIDC.
