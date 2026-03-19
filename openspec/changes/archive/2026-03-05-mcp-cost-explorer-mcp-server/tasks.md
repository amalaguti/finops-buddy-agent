## 1. Settings and configuration

- [x] 1.1 Add Cost Explorer MCP settings in `src/finops_agent/settings.py`: constants for default package (`awslabs.cost-explorer-mcp-server@latest`), caches for enabled and command; env helpers `_env_cost_explorer_mcp_enabled`, `_env_cost_explorer_mcp_command`; parser `_parse_cost_explorer_mcp_command`; getters `get_cost_explorer_mcp_enabled()` (default False) and `get_cost_explorer_mcp_command()` with platform-specific default (Windows `--from` + `.exe` as for Billing/Documentation). Wire `reset_settings_cache` to clear the new caches.
- [x] 1.2 Update `config/settings.yaml` template: add commented block for Cost Explorer MCP with `agent.cost_explorer_mcp_enabled: false`, `agent.cost_explorer_mcp_command`, and env vars `FINOPS_MCP_COST_EXPLORER_ENABLED`, `FINOPS_MCP_COST_EXPLORER_COMMAND`; note that BCM MCP covers Cost Explorer and this server is optional, disabled by default.

## 2. Agent runner integration

- [x] 2.1 In `src/finops_agent/agent/runner.py`: import `get_cost_explorer_mcp_enabled` and `get_cost_explorer_mcp_command` from settings; implement `create_cost_explorer_mcp_client(session)` (stdio transport, pass AWS_PROFILE/AWS_REGION from session, set `_finops_mcp_server_name` to "AWS Cost Explorer MCP Server"); add constant for display name if needed for tool callback.
- [x] 2.2 In `build_agent` and `run_chat_loop`: when building the tools list, create Cost Explorer MCP client when enabled and append to tools (same order pattern as other MCPs). Ensure Cost Explorer MCP is included in MCP names for welcome/status/tooling.

## 3. Documentation

- [x] 3.1 Document in README.md (Configuration / Settings and environment): `FINOPS_MCP_COST_EXPLORER_ENABLED`, `FINOPS_MCP_COST_EXPLORER_COMMAND`; YAML keys `agent.cost_explorer_mcp_enabled`, `agent.cost_explorer_mcp_command`; note that the Cost Explorer MCP is optional and disabled by default, and that BCM MCP already covers Cost Explorer–style functionality.

## 4. Lint and format

- [x] 4.1 Run `poetry run ruff check .` and `poetry run ruff format .`; fix any issues.

## 5. Tests

- [x] 5.1 In `tests/test_settings.py`: add tests for Cost Explorer MCP — default disabled when no config; enabled via YAML; enabled/disabled via `FINOPS_MCP_COST_EXPLORER_ENABLED`; command default and override via `FINOPS_MCP_COST_EXPLORER_COMMAND`; cache reset clears Cost Explorer caches (map to spec scenarios).
- [x] 5.2 In `tests/test_agent.py`: add tests — `create_cost_explorer_mcp_client` returns None when disabled; when enabled, agent build includes Cost Explorer MCP client (mock getters and create function as for Billing/Documentation).
- [x] 5.3 If chat CLI tests assert MCP list or status, update or add cases so Cost Explorer MCP appears in /tooling and /status when enabled.
