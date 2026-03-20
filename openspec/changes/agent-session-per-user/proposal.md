## Why

The HTTP API and agent runtime today assume a **single global agent/tool session** (e.g. tied to `FINOPS_MASTER_PROFILE` and warm-up caches). That matches **desktop single-user** use but is unsafe for **multi-user cloud deployment**: concurrent `/chat` requests can **share or bleed** conversation context and cached agent state. The `deploy-aws` design adds OIDC identity at the edge but does not yet require **isolated agent sessions per user** (or per explicit session id).

## What Changes

- Introduce a **session abstraction** for the agent and related caches (tools, warm-up state), keyed by a **stable request identity** (e.g. ALB OIDC subject) or by an explicit **session id** when anonymous/local.
- Ensure **no cross-user reuse** of Strands agent instances, conversation buffers, or MCP client pools keyed only to “one global server process.”
- Preserve **backward-compatible single-user local** behavior when trusted-proxy identity is absent (one default session key).
- **BREAKING** potential: any code that assumed a single global singleton for agent state must move behind the session registry; external API contract may gain optional `session` header or cookie (design phase).

## Capabilities

### New Capabilities

- `agent-session-isolation`: Requirements for scoped agent runtime, cache keys, and chat state per user/session.

### Modified Capabilities

- `chat-agent`: Align warm-up, agent builder usage, and tool provider lifetime with per-session lifecycle.
- `backend-api`: Resolve session key from identity headers or defaults; document interaction with streaming endpoints.

## Impact

- `src/finops_buddy/agent/` (builder, chat loop, any global caches), FastAPI lifespan/warm-up, tests for concurrent chat isolation.
