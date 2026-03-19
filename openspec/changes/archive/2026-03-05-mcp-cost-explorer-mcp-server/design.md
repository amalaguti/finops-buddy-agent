# Design: Cost Explorer MCP Server (disabled by default)

## Context

The agent already integrates optional MCP servers: Knowledge (remote), Billing/Cost Management (local uvx), and Documentation (local uvx). Each is controlled by settings (`agent.<name>_mcp_enabled`, `agent.<name>_mcp_command`) and env vars (`FINOPS_MCP_*_ENABLED`, `FINOPS_MCP_*_COMMAND`). Billing and Documentation default to **disabled**; Knowledge defaults to enabled. The Cost Explorer MCP server ([awslabs/mcp cost-explorer-mcp-server](https://github.com/awslabs/mcp/tree/main/src/cost-explorer-mcp-server)) provides Cost Explorer–specific tools (e.g. get_cost_and_usage, get_cost_forecast). BCM MCP already covers Cost Explorer–style use cases; this change adds the standalone Cost Explorer MCP as an optional, **disabled-by-default** integration so users can enable it if desired.

## Goals / Non-Goals

**Goals:**

- Add Cost Explorer MCP server as an optional tool source, disabled by default.
- Reuse the same configuration and runtime pattern as Billing and Documentation MCP (YAML + env, stdio transport via uvx, session env for AWS profile/region).
- Expose the new server in `/tooling` and `/status` when enabled.
- Document the new settings and that BCM overlaps Cost Explorer; recommend BCM for most users.

**Non-Goals:**

- Changing default behavior for existing MCPs or in-process cost tools.
- Supporting a different transport (e.g. remote URL) for Cost Explorer MCP in this change.
- Resolving overlap between BCM and Cost Explorer MCP in the agent prompt; both can be enabled simultaneously if the user chooses.

## Decisions

1. **Default: disabled.** Cost Explorer MCP SHALL default to off (`cost_explorer_mcp_enabled` false, `FINOPS_MCP_COST_EXPLORER_ENABLED` not set → false). Rationale: Align with project decision that BCM covers Cost Explorer; avoid surprising users with an extra MCP and potential duplicate tools unless they opt in.

2. **Same pattern as Billing/Documentation.** Use `get_cost_explorer_mcp_enabled()` and `get_cost_explorer_mcp_command()` in settings; `create_cost_explorer_mcp_client(session)` in runner; append client to tools when enabled; pass session env (AWS_PROFILE, AWS_REGION) into the subprocess. Rationale: Consistency and minimal new concepts; reuse of platform-specific uvx defaults (e.g. Windows `--from` + `.exe`).

3. **Default command.** Default uvx package: `awslabs.cost-explorer-mcp-server@latest`. Command parsing via `shlex.split` and same Windows vs non-Windows handling as Documentation/Billing. Rationale: PyPI package name is `awslabs.cost-explorer-mcp-server`; uvx follows the same pattern as other awslabs MCP servers.

4. **Display name.** Use a single display name for tool attribution and status (e.g. "AWS Cost Explorer MCP Server"). Rationale: Matches how other MCPs are presented in `/tooling` and `/status`.

5. **No tool-name mapping in callback.** If Cost Explorer MCP tools use a distinct prefix or naming, we can add a small mapping in `_mcp_server_name_for_tool` (or equivalent) so that tool invocations show the correct MCP name; otherwise rely on the existing `_finops_mcp_server_name` attribute on the client. Rationale: Implement once we see actual tool names from the server; optional polish.

## Risks / Trade-offs

- **Duplicate capabilities:** If both BCM and Cost Explorer MCP are enabled, the agent may see overlapping tools. Mitigation: Document that BCM covers Cost Explorer; Cost Explorer MCP is optional and off by default; users enable at their own choice.
- **Extra process when enabled:** One more subprocess when enabled. Mitigation: Same as other stdio MCPs; no change to behavior when disabled.
- **Package/version:** We depend on `awslabs.cost-explorer-mcp-server` from PyPI/uvx. Mitigation: Pin or document `@latest`; same approach as Billing/Documentation.

## Migration Plan

- No data migration. Add new settings and code paths; existing configs unchanged.
- Rollback: Remove Cost Explorer MCP wiring and settings; no persisted state to migrate back.

## Open Questions

- None. Tool-name-to-server display mapping can be refined after implementation if the Cost Explorer MCP uses a specific naming convention.
