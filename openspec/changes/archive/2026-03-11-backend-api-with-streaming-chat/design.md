## Context

The FinOps Agent is a CLI application that uses shared Python modules for AWS identity, costs, and a Strands-based chat agent. The CLI runs in a single process: it resolves credentials (env, `AWS_PROFILE`, settings), builds the agent and MCP clients once per session, and runs an interactive loop. There is no HTTP layer today. PROJECT_CONTEXT envisions a Phase 2 backend (HTTP API around the same core) and then a React frontend. This design adds that backend with read-only endpoints and streaming chat, in single-user mode, reusing the existing profile and credential model.

## Goals / Non-Goals

**Goals:**

- Expose profiles, context, and current-month costs over HTTP so a future UI can call them without invoking the CLI.
- Expose chat over HTTP with streaming (e.g. SSE or WebSocket) so the UI can show tokens or chunks as they arrive.
- Single-user mode: one logical user; credentials and profile selection work like the CLI (process env, optional profile query/header).
- Reuse all existing `finops_agent` code (identity, costs, agent builder, MCP); the API is a thin HTTP adapter.
- Document backend-specific config (host, port, CORS) in README and `config/settings.yaml`; use FINOPS_ prefix for any new env vars.

**Non-Goals:**

- Multi-user auth, tenant isolation, or user-bound credentials. Out of scope for this change.
- Persistence of chat history or conversation store (in-memory per request or per session is enough).
- Changing how the CLI works; CLI remains the primary entrypoint for terminal users.

## Decisions

### 1. HTTP framework: FastAPI + Uvicorn

Use **FastAPI** for routing, request/response models, and dependency injection; **Uvicorn** as the ASGI server. Alternatives: Flask (no async-native streaming), Starlette (lower-level). FastAPI gives OpenAPI docs, type-safe request bodies, and straightforward SSE/streaming support.

### 2. Profile and credentials (single-user, CLI-like)

- **Credentials**: Backend process uses the same sources as the CLI: `AWS_PROFILE`, `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY`/`AWS_SESSION_TOKEN`, and settings file (e.g. excluded/included profiles). No new auth system.
- **Profile selector**: For endpoints that need a profile (context, costs, chat), accept an optional `profile` query parameter or `X-AWS-Profile` header. If absent, use `AWS_PROFILE` from the environment (or first available profile). Same semantics as CLI `--profile`.
- **Single-user**: One process, one effective user. No login or per-user identity; optional future extension via headers or auth is not part of this change.

### 3. Read-only endpoints

- **GET /profiles** — Returns list of profile names (after applying excluded/included settings). No request body; optional query for consistency with other endpoints. Reuses `list_profiles()`.
- **GET /context** — Returns account context (account_id, arn, role, master/payer hint). Optional query `profile`. Reuses `get_account_context(profile_name=...)`.
- **GET /costs** — Returns current-month costs by service. Optional query `profile`. Reuses `get_costs_by_service(session)`. Response shape: list of `{ "service": str, "cost": float }` or similar; errors return 4xx/5xx with a clear message.

All three use the same pattern: resolve session from profile (or default), call existing module, return JSON. No new business logic.

### 4. Chat and streaming

- **Option A — SSE (Server-Sent Events)**: One endpoint, e.g. **POST /chat** with body `{ "message": "..." }` and optional `profile`. Response: `Content-Type: text/event-stream`; events carry text chunks (or full message if streaming is not available from Strands). Client can send multiple POSTs for multi-turn; server does not maintain conversation state across requests unless we add a session id (optional for v1: stateless POST per message with conversation history in request body, or single-turn only for minimal v1).
- **Option B — WebSocket**: Single connection; client sends messages, server streams agent replies. Keeps conversation state on the server for the connection lifetime. More complex (connection lifecycle, reconnects) but natural for multi-turn chat.

**Decision:** Prefer **SSE** for v1: simpler (single HTTP request per user message), easy to add a request body field for conversation history (e.g. `messages: [{ role, content }]`) so the client drives multi-turn. If the Strands agent exposes a stream, iterate over it and emit SSE events (e.g. one event per chunk or per token); otherwise, run the agent once and send one or more SSE events with the full text. Add **optional** `conversation_id` or `messages` in the request later if we want server-side conversation state without WebSockets.

### 5. Agent lifecycle for chat

- **Per-request**: For each POST /chat, create a session (from profile), build tools and MCP clients, build agent, run one turn (or stream), then tear down. No long-lived agent process. Matches stateless API; downside is cold start per request (MCP and model load). Acceptable for single-user v1.
- **Alternative (deferred):** Pool or keep one agent per profile; requires background worker or long-lived process and clearer lifecycle; out of scope for this change.

### 6. Backend configuration

- **Settings file**: Optional `server` (or `api`) section in `config/settings.yaml`: e.g. `host`, `port`, `cors_origins`. Keys and structure to be defined in implementation; template in `config/settings.yaml` and README.
- **Environment**: Any new options use FINOPS_ prefix (e.g. `FINOPS_SERVER_PORT`, `FINOPS_SERVER_HOST`). Env overrides file.
- **Default**: Listen on `127.0.0.1:8000` or similar; CORS disabled or allow same-origin only by default so the UI can be developed on the same host.

### 7. How to run the server

- **CLI subcommand**: Add `finops serve` (or `finops api`) that invokes uvicorn with the FastAPI app. Keeps one entrypoint (`finops`) for both CLI and server.
- **Alternative**: Document `uvicorn finops_agent.api:app` for advanced users; prefer `finops serve` for consistency.

## Risks / Trade-offs

- **[Risk] Cold start per chat request**: Building the agent and MCP clients on every POST /chat can be slow (seconds). Mitigation: Document; accept for v1; consider agent reuse or pooling in a future change.
- **[Risk] Strands may not expose token-level streaming**: If the agent returns only a full response, we stream it as one or a few SSE events (e.g. one event with the full text). Mitigation: Design the SSE contract so clients can handle both chunked and single-message streams.
- **[Trade-off] No conversation persistence**: Multi-turn can be done by sending prior messages in the request body; server does not store history. Reduces complexity; persistence can be added later if needed.
- **[Risk] CORS and network exposure**: Default bind to 127.0.0.1 and strict CORS reduce exposure. Mitigation: Document that for production use, put the API behind a reverse proxy and auth if needed.

## Migration Plan

- Add new dependency (FastAPI, uvicorn) to pyproject.toml; no change to existing CLI behavior.
- New code lives under `finops_agent/api/` (or `finops_agent/server/`); CLI gains `serve` subcommand that runs the app.
- No data migration. Rollback: remove the serve subcommand and API module, drop the new dependency.

## Open Questions

- Exact SSE event schema (e.g. `data: {"chunk": "..."}` vs `data: <text>`) and whether to include usage/metadata in a final event.
- Whether to support a `messages` array in POST /chat for multi-turn in v1 (recommended: yes, so the UI can send full history and keep stateless server).
