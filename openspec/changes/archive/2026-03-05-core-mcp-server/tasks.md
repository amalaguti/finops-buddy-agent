# Tasks: core-mcp-server

## 1. Branch and setup

- [x] 1.1 Create a feature branch (e.g. `feature/core-mcp-server`) and do not implement on `main`. Switch to the branch before implementing.

## 2. Settings: Core MCP resolution

- [x] 2.1 In `src/finops_agent/settings.py`, add caches and getters for Core MCP: `get_core_mcp_enabled()`, `get_core_mcp_command()` (returning (command, args)), and `get_core_mcp_roles()` (returning list of role strings). Resolve from YAML (`agent.core_mcp_enabled`, `agent.core_mcp_command`, `agent.core_mcp_roles`) and env (`FINOPS_MCP_CORE_ENABLED`, `FINOPS_MCP_CORE_COMMAND`, `FINOPS_MCP_CORE_ROLES`). Default enabled false; default roles `[finops, aws-foundation, solutions-architect]` when unset; default command uvx for `awslabs.core-mcp-server@latest` with platform-specific args (Windows if needed). Include cache invalidation in `reset_settings_cache()`.
- [x] 2.2 Add or update `config/settings.yaml` with Core MCP template: `agent.core_mcp_enabled`, `agent.core_mcp_command`, `agent.core_mcp_roles` (commented or placeholder), and document env vars in comments.

## 3. Agent runner: Core MCP client and build logic

- [x] 3.1 In `src/finops_agent/agent/runner.py`, add `create_core_mcp_client(session)` that when Core is enabled creates an MCPClient via stdio using `get_core_mcp_command()` and env that includes `AWS_PROFILE`, `AWS_REGION` (from session) and each role from `get_core_mcp_roles()` as `role_name=true`. Set `_finops_mcp_server_name` to a string that includes the configured roles (e.g. `"Core MCP Server (roles: finops, aws-foundation, solutions-architect)"`).
- [x] 3.2 In `build_agent()` (and any other code path that assembles tools): when Core MCP is enabled, do not attach Billing, Cost Explorer, or Pricing MCP clients; set `include_cost_tools = (billing_client is None and core_client is None)` (or equivalent) so built-in cost tools are omitted when Core is enabled. Attach Core MCP client when enabled (alongside Knowledge, Documentation as today).
- [x] 3.3 Ensure startup progress (e.g. "Loading Core MCP...") is emitted when Core MCP is being loaded, consistent with other MCP servers.

## 4. /tooling and /status display

- [x] 4.1 Verify that `/tooling` and `/status` use the MCP client’s `_finops_mcp_server_name` for Core so the display shows "Core MCP Server (roles: …)" and readiness; no extra change needed if the existing mechanism already uses that attribute.

## 5. Documentation and config template

- [x] 5.1 Document Core MCP in README.md: Configuration section (settings file keys `agent.core_mcp_*` and env vars `FINOPS_MCP_CORE_ENABLED`, `FINOPS_MCP_CORE_COMMAND`, `FINOPS_MCP_CORE_ROLES`), that when Core is enabled the standalone Billing, Cost Explorer, and Pricing MCPs are not attached, and that `/tooling` and `/status` show Core and its roles. Link to AWS Core MCP Server docs if desired.
- [x] 5.2 Ensure `config/settings.yaml` includes all Core MCP keys (see 2.2).

## 6. Lint and format

- [x] 6.1 Run `poetry run ruff check .` and `poetry run ruff format .`; fix any issues.

## 7. Tests

- [x] 7.1 Add or extend pytest tests in `tests/test_settings.py` for Core MCP: get_core_mcp_enabled default false; enabled via YAML; env overrides YAML; get_core_mcp_roles default and override from YAML and env; get_core_mcp_command default and override; reset_settings_cache clears Core MCP caches.
- [x] 7.2 Add or extend pytest tests in `tests/test_agent.py` (and optionally `tests/test_chat_cli.py`) for Core MCP: agent built with Core client when enabled; agent built without Billing/Pricing/Cost Explorer clients when Core enabled; built-in cost tools omitted when Core enabled; Core MCP appears in /tooling and /status with roles when enabled; startup progress includes Core when enabled. Name tests after spec scenarios where practical.
