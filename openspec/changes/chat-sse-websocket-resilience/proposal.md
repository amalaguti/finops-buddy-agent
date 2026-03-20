## Why

**SSE** behind an ALB with **sticky sessions** is fragile at scale: **Fargate task restarts** or **target churn** drop long-lived streams; a single FinOps chat turn can take **30–60+ seconds** (MCP warm-up + LLM). Users see opaque failures without **client reconnect** semantics. **WebSockets** are first-class on ALB and may reduce reliance on stickiness for some patterns.

## What Changes

- **Frontend:** SSE client supports **reconnect** with **`Last-Event-ID`** (or equivalent) when the server exposes resumable semantics; UX for “reconnecting…” during long runs.
- **Backend:** Document and implement **idempotent resume** or clear **non-resumable** contract; optional **WebSocket** chat transport alongside or instead of SSE for cloud deployments.
- Coordinate with **agent session isolation** so reconnects attach to the **same logical session**.

## Capabilities

### New Capabilities

- `chat-stream-resilience`: Requirements for SSE reconnect, optional Last-Event-ID, and optional WebSocket chat for production.

### Modified Capabilities

- `hosted-web-ui`: Client streaming transport behavior and reconnection.
- `backend-api`: Server streaming contract, headers, optional WS endpoint.

## Impact

- `frontend/` (SSE client), `src/finops_buddy/api/`, WebSocket middleware if added, nginx/alb documentation in deployment docs.
