## 1. Settings and configuration

- [x] 1.1 Add Pricing MCP settings in `src/finops_agent/settings.py`: constants for default package (`awslabs.aws-pricing-mcp-server@latest`), caches for enabled and command; env helpers `_env_pricing_mcp_enabled`, `_env_pricing_mcp_command`; parser `_parse_pricing_mcp_command`; getters `get_pricing_mcp_enabled()` (default False) and `get_pricing_mcp_command()` with platform-specific default (Windows `--from` + `.exe` as for Billing/Documentation). Wire `reset_settings_cache` to clear the new caches.
- [x] 1.2 Update `config/settings.yaml` template: add commented block for Pricing MCP with `agent.pricing_mcp_enabled: false`, `agent.pricing_mcp_command`, and env vars `FINOPS_MCP_PRICING_ENABLED`, `FINOPS_MCP_PRICING_COMMAND`; note that the server is optional, disabled by default, and requires IAM `pricing:*` when enabled.

## 2. Agent runner integration

- [x] 2.1 In `src/finops_agent/agent/runner.py`: import `get_pricing_mcp_enabled` and `get_pricing_mcp_command` from settings; implement `create_pricing_mcp_client(session)` (stdio transport, pass AWS_PROFILE/AWS_REGION from session, set `_finops_mcp_server_name` to "AWS Pricing MCP Server"); add constant for display name if needed for tool callback.
- [x] 2.2 In `build_agent` and `run_chat_loop`: when building the tools list, create Pricing MCP client when enabled and append to tools (same order pattern as other MCPs). Ensure Pricing MCP is included in MCP names for welcome/status/tooling.

## 3. Documentation

- [x] 3.1 Document in README.md (Configuration / Settings and environment): `FINOPS_MCP_PRICING_ENABLED`, `FINOPS_MCP_PRICING_COMMAND`; YAML keys `agent.pricing_mcp_enabled`, `agent.pricing_mcp_command`; note that the Pricing MCP is optional and disabled by default, and that IAM `pricing:*` (and optionally AWS credentials) are required when enabled.

## 4. Lint and format

- [x] 4.1 Run `poetry run ruff check .` and `poetry run ruff format .`; fix any issues.

## 5. Tests

- [x] 5.1 In `tests/test_settings.py`: add tests for Pricing MCP — default disabled when no config; enabled via YAML; enabled/disabled via `FINOPS_MCP_PRICING_ENABLED`; command default and override via `FINOPS_MCP_PRICING_COMMAND`; cache reset clears Pricing MCP caches (map to spec scenarios).
- [x] 5.2 In `tests/test_agent.py`: add tests — `create_pricing_mcp_client` returns None when disabled; when enabled, agent build includes Pricing MCP client (mock getters and create function as for Billing/Documentation).
- [x] 5.3 If chat CLI tests assert MCP list or status, update or add cases so Pricing MCP appears in /tooling and /status when enabled.
