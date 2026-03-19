# Design: Defer warm-up, demo ARN mask, env sample

## Context

The FastAPI app currently calls `warm_chat_agent_on_startup()` at module import time when `FINOPS_AGENT_WARM_ON_STARTUP` is true. That builds the Strands agent and initializes MCP tool providers (e.g. billing-cost-management-mcp), which can take tens of seconds and blocks the importing thread. Any import of `finops_buddy.api` (e.g. tests that use `from finops_buddy.api.demo import ...`) therefore triggers this path and causes pytest collection to hang. Demo mode already masks account IDs and profile names; the ARN string in the account context response still contained the assumed-role session name (often an email). There was no committed env template for users.

## Goals / Non-Goals

**Goals:**

- Run agent warm-up only when the ASGI server starts (uvicorn lifespan), not when the app module is imported.
- In demo mode, mask the ARN's assumed-role session name (e.g. replace with `john.doe@finops.buddy`) so the account details pane does not expose PII.
- Provide a sanitized `env.local.sample` at repo root and document it.

**Non-Goals:**

- Changing when or how MCP servers are started once the app runs (only when warm runs).
- Adding new env vars; the sample documents existing FINOPS_* vars only.
- Changing demo account-ID or profile-name masking logic beyond the ARN session name.

## Decisions

1. **Use FastAPI lifespan for warm-up**  
   Use an `@asynccontextmanager` lifespan passed to `FastAPI(lifespan=...)`. In the startup phase (before `yield`), if `get_agent_warm_on_startup()` is true, call `warm_chat_agent_on_startup()`. This runs only when uvicorn (or another ASGI server) starts the app, not when the module is imported.  
   *Alternative:* Keep warm at import but gate with a "running under pytest" check (e.g. `"pytest" in sys.modules`). Rejected because it is fragile and does not help other importers (e.g. scripts, other test runners).

2. **Mask ARN session name in demo layer**  
   In `finops_buddy.api.demo`, when masking the `arn` key in response data, after applying existing account-ID substitution in the string, detect assumed-role ARNs (e.g. containing `assumed-role/` or `:assumed-role/`) and replace the segment after the last `/` with a constant (e.g. `DEMO_MASK_ARN_SESSION_NAME = "john.doe@finops.buddy"`). Reuse the existing `mask_response_data` / `_mask_dict` path so the context endpoint’s `arn` field is masked when `X-Demo-Mode: true` is set.  
   *Alternative:* Mask in the frontend. Rejected so a single source of truth stays in the backend and any future API consumers also get masked data.

3. **Env sample as `env.local.sample` (no leading dot)**  
   Add a single file at project root named `env.local.sample` with placeholder values for all FINOPS_* variables used by the app, so users can copy to `.env.local`. Use a non-hidden filename so it is clearly visible in the repo and in docs.  
   *Alternative:* `.env.local.sample`. Rejected per user preference for a non-hidden file.

## Risks / Trade-offs

- **[Risk]** Lifespan runs only when the app is actually started (e.g. uvicorn). Test suites that only import the app and never run the server will not run warm-up, which is desired.  
  *Mitigation:* None needed; tests that need a warmed agent can start the app (e.g. TestClient with lifespan) if required.

- **[Risk]** ARN masking is heuristic (look for last `/` in assumed-role ARNs). Unusual ARN formats could be mishandled.  
  *Mitigation:* Logic is scoped to strings that contain `assumed-role/` or `:assumed-role/`; others are only subject to existing account-ID replacement.

- **[Trade-off]** `env.local.sample` must be kept in sync when new FINOPS_* vars are added.  
  *Mitigation:* Document in README and in OpenSpec/tasks that new env vars should update the sample.

## Migration Plan

- No data or config migration. Deploy as a normal release.
- Rollback: revert the lifespan change to restore module-level warm (would reintroduce pytest hang unless warm is disabled via env).

## Open Questions

None; implementation is straightforward and already done.
