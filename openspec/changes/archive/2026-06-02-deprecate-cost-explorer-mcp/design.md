## Context

FinOps Buddy added optional Cost Explorer MCP integration (disabled by default) because BCM MCP already covers Cost Explorer APIs. AWS has since **deprecated and yanked** `awslabs.cost-explorer-mcp-server` on PyPI; the replacement is `awslabs.billing-cost-management-mcp-server`, already integrated.

## Goals / Non-Goals

**Goals:**

- Prevent agent startup failures or silent broken MCP loads from the yanked package.
- Guide users who still have `FINOPS_MCP_COST_EXPLORER_ENABLED=true` toward Billing MCP.
- Keep env/YAML keys parseable (no crash on existing configs) but non-functional for attachment.

**Non-Goals:**

- Migrating user configs automatically (e.g. auto-enabling Billing when Cost Explorer was enabled).
- Removing BCM or Core MCP integration.
- Changing in-process Cost Explorer API usage in `costs.py` (dashboard/CLI) — that is unrelated to MCP.

## Decisions

### 1. Remove client wiring; do not redirect at runtime

**Decision:** Remove `create_cost_explorer_mcp_client` usage from all agent build paths. Do not auto-enable Billing MCP when Cost Explorer was requested.

**Rationale:** Billing MCP is heavier and changes tool surface; users may have intentionally disabled it. A warning + docs is sufficient.

### 2. Deprecation surface in settings

**Decision:** Keep `get_cost_explorer_mcp_enabled()` but it **always returns `False`**. If env or YAML requests enable, emit a `logger.warning` with migration link. Remove `get_cost_explorer_mcp_command()` and `DEFAULT_COST_EXPLORER_MCP_PACKAGE`.

**Rationale:** Backward-compatible config files; clear operator feedback without failing startup.

### 3. Spec delta: REMOVED requirements

**Decision:** Delta spec marks attachment, command override, and /tooling visibility requirements as **REMOVED**; add new requirement for deprecation warning when enable is requested.

## Risks / Trade-offs

- Users who relied on Cost Explorer MCP namespace tools (`cost_explorer_*`) must use BCM tools instead → Mitigation: warning message names Billing MCP env var.
- **Breaking** for anyone who pinned a non-yanked Cost Explorer version via custom command → Acceptable; package is officially deprecated.

## Migration Plan

1. Ship code + doc updates.
2. Users with `FINOPS_MCP_COST_EXPLORER_ENABLED=true` see warning; set `FINOPS_MCP_BILLING_ENABLED=true` instead.
3. Remove deprecated settings keys in a future major release (out of scope).
