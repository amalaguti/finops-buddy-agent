# Proposal: Cost Explorer MCP Server (disabled by default)

## Why

The project context (PROJECT_CONTEXT.md) states that the standalone Cost Explorer MCP server is not added because the Billing and Cost Management (BCM) MCP server already covers Cost Explorer functionality. We want to implement the **Cost Explorer MCP server** anyway so it is available as an option (e.g. for users who prefer the dedicated Cost Explorer API surface or run it separately), but keep it **disabled by default** via settings and environment variables so that default behavior and documentation remain aligned with “BCM covers cost/cost-explorer.”

## What Changes

- Add support for the AWS Cost Explorer MCP server ([awslabs/mcp cost-explorer-mcp-server](https://github.com/awslabs/mcp/tree/main/src/cost-explorer-mcp-server)), run locally via `uvx` (same pattern as Billing and Documentation MCP).
- **Default: disabled.** New settings and env vars SHALL default to `false` / off so the server is not started unless explicitly enabled.
- Settings: add `agent.cost_explorer_mcp_enabled` (default false) and optional `agent.cost_explorer_mcp_command`; env: `FINOPS_MCP_COST_EXPLORER_ENABLED`, `FINOPS_MCP_COST_EXPLORER_COMMAND`.
- Wire the Cost Explorer MCP client into the agent builder and chat loop when enabled (same pattern as Billing/Documentation MCP): stdio transport, pass AWS profile/region from session.
- Update `config/settings.yaml` template and README with the new options; document that BCM MCP overlaps Cost Explorer and this server is optional, off by default.

## Capabilities

### New Capabilities

- **mcp-cost-explorer**: Optional integration with the AWS Cost Explorer MCP server. When enabled via settings/env, the agent can use Cost Explorer MCP tools (e.g. get_cost_and_usage, get_cost_forecast). Default is disabled; YAML and env use the same pattern as Billing/Documentation MCP (enabled flag + optional command).

### Modified Capabilities

- **app-settings**: Add resolution for Cost Explorer MCP: `agent.cost_explorer_mcp_enabled` (default false), `agent.cost_explorer_mcp_command` (optional), and env vars `FINOPS_MCP_COST_EXPLORER_ENABLED`, `FINOPS_MCP_COST_EXPLORER_COMMAND`. Same precedence as existing MCP settings (env overrides file).

## Impact

- **Code**: `src/finops_agent/settings.py` (new getters and caches), `src/finops_agent/agent/runner.py` (create_cost_explorer_mcp_client, wire into build_agent and run_chat_loop; include in MCP status/tooling).
- **Config**: `config/settings.yaml` template gains commented Cost Explorer MCP block.
- **Docs**: README Configuration section documents the new env vars and YAML keys; note that BCM covers Cost Explorer and this server is optional, disabled by default.
- **Tests**: New/updated tests in `tests/test_settings.py`, `tests/test_agent.py`, and any chat CLI tests that assert MCP listing.
