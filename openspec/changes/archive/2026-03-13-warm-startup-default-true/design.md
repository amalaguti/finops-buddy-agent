## Context

The chat API (`src/finops_buddy/api/app.py`) supports an optional warm-up step at startup via `FINOPS_AGENT_WARM_ON_STARTUP`. When enabled, `warm_chat_agent_on_startup()` pre-builds the Strands agent, loads MCP tools, and caches the profile-to-account mapping. This eliminates cold-start latency on the first chat request.

Currently:
- Default is **off** (empty string treated as falsy)
- Setting is not documented in README.md or `config/settings.yaml`
- No YAML settings file support exists; it's env-only

## Goals / Non-Goals

**Goals:**
- Default `FINOPS_AGENT_WARM_ON_STARTUP` to `true` so warm-up happens by default
- Add YAML settings support (`agent.warm_on_startup`) with env override
- Document the setting in README.md and `config/settings.yaml` template
- Follow existing settings patterns (env overrides YAML, truthy string parsing)

**Non-Goals:**
- Changing what `warm_chat_agent_on_startup()` does internally
- Adding warm-up to CLI mode (this is API-specific)
- Making warm-up async or lazy (current sync warm-up is acceptable)

## Decisions

### 1. Default to true when no value provided

**Decision**: When neither YAML nor environment provides a value, default to `true`.

**Rationale**: The warm-up improves first-request latency with minimal downside. Users running the API server generally want the best UX. Those with special constraints (e.g., minimal containers) can explicitly set `false`.

**Alternative considered**: Keep default `false` and just document. Rejected because the warm-up benefit outweighs the small startup delay.

### 2. Use existing settings.py resolution pattern

**Decision**: Add `get_agent_warm_on_startup() -> bool` to `settings.py`, following the pattern of `get_cost_explorer_mcp_enabled()`:
1. Check `FINOPS_AGENT_WARM_ON_STARTUP` env var (truthy values: `1`, `true`, `yes`)
2. Fall back to YAML `agent.warm_on_startup` (boolean)
3. Fall back to default `True`

**Rationale**: Consistency with existing settings resolution. Env override allows runtime control without changing config files.

### 3. Update app.py to call the resolver

**Decision**: Replace the inline `os.environ.get(...)` check in `app.py` with a call to `get_agent_warm_on_startup()`.

**Rationale**: Centralizes settings logic, enables YAML support, and aligns with how other settings are resolved.

## Risks / Trade-offs

- **[Slightly longer startup]** Warm-up adds ~1-3 seconds to API startup when `FINOPS_MASTER_PROFILE` is set. → Acceptable; user can disable with `FINOPS_AGENT_WARM_ON_STARTUP=false`.
- **[Behavior change for existing users]** Users who previously relied on no warm-up (default off) will now get warm-up. → Generally positive; document in change notes.
- **[Warm-up failure is silent]** If warm-up fails, the API still starts (best-effort). → Existing behavior; no change needed.
