# Backend API with Streaming Chat — Proposal

## Why

The FinOps Agent today is CLI-only. To support a future web UI (e.g. React), we need an HTTP API that exposes the same capabilities: list profiles, account context, current-month costs, and the chat agent. Doing the backend first gives the UI a stable contract and centralizes the hard parts (session, credentials, streaming chat) in one place. Single-user mode keeps scope manageable while preserving the same profile and credential model as the CLI (e.g. `AWS_PROFILE`, settings file, `FINOPS_*` env).

## What Changes

- Add an **HTTP API** (e.g. FastAPI) that reuses the existing `finops_agent` core (identity, costs, agent builder, chat loop).
- **Read-only endpoints**: List profiles, account context (optionally for a given profile), current-month costs by service (for a given profile). Profile and credentials are supplied in a similar fashion to the CLI (e.g. query/header for profile, backend process env for credentials).
- **Chat with streaming**: One or more endpoints or a WebSocket/SSE channel for chat. The agent response is streamed to the client (e.g. token-by-token or chunk-by-chunk) so the UI can show progress. Single-user mode: one logical user; profile/credentials handled like the CLI (e.g. default or specified per request).
- **No new auth system**: Single-user mode; backend runs with the same credential sources as the CLI (env, `AWS_PROFILE`, settings). Optional query/header to select profile when multiple are configured.
- **Configuration**: Reuse existing settings and `FINOPS_*` env; optional backend-specific settings (e.g. host/port, CORS) documented and in `config/settings.yaml` template.

## Capabilities

### New Capabilities

- **backend-api**: The system SHALL expose an HTTP API that provides (1) list of AWS profiles (honoring existing excluded/included settings), (2) account context for a given or default profile, (3) current-month costs by service for a given or default profile, and (4) chat with the Strands agent with streaming responses. The API SHALL operate in single-user mode with profile and credentials managed in a similar fashion to the CLI (backend process environment and optional profile selector). Configuration SHALL use existing app settings and FINOPS_ prefix; backend-specific options (e.g. bind address, port, CORS) SHALL be documented in README and config/settings.yaml.

### Modified Capabilities

- None. Existing specs (aws-identity, chat-agent, costs-this-month, app-settings) describe behavior; the backend is a new entrypoint that reuses the same requirements.

## Impact

- **Dependencies**: New runtime dependency for the HTTP server (e.g. FastAPI, uvicorn); no change to Strands or MCP.
- **Code**: New package or module for the API (e.g. `finops_agent/api/` or `finops_agent/server/`), plus a way to run the server (e.g. `finops serve` subcommand or `uvicorn` entrypoint). Existing modules (identity, costs, agent runner) remain the source of truth; API layer only adapts I/O.
- **Configuration**: Optional backend section in settings and env (e.g. host, port, CORS); README and config/settings.yaml template updated.
- **Testing**: Unit tests for API routes and streaming behavior; optional integration test against a running server.
