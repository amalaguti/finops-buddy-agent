## Why

The AWS Cost Explorer MCP Server PyPI package (`awslabs.cost-explorer-mcp-server@latest`) is **deprecated and yanked**. `uvx` installs fail or are unreliable, so users who enable `FINOPS_MCP_COST_EXPLORER_ENABLED` cannot start the agent MCP stack as intended. AWS directs all users to the **Billing and Cost Management MCP Server**, which FinOps Buddy already supports via `FINOPS_MCP_BILLING_ENABLED`.

## What Changes

- **Remove** Cost Explorer MCP client attachment from agent startup (`finops chat`, `build_agent_and_tools`, `build_agent`).
- **Deprecate** Cost Explorer MCP settings: `FINOPS_MCP_COST_EXPLORER_ENABLED` and `FINOPS_MCP_COST_EXPLORER_COMMAND` (and YAML equivalents) are **ignored**; when set to enable, log a one-time warning pointing to Billing MCP and the [AWS migration guide](https://github.com/awslabs/mcp/blob/main/docs/migration-cost-explorer.md).
- **Remove** default `uvx` command for the yanked package from `settings.py`.
- **Remove** Cost Explorer MCP tool names from the read-only guardrail allow-list (no longer reachable).
- Update **`docs/CONFIGURATION.md`**, **`docs/MCP.md`**, and **`config/settings.yaml`** to document removal and the Billing MCP replacement.
- **BREAKING**: Enabling Cost Explorer MCP no longer attaches any server; users must use Billing MCP (or Core MCP with `finops` role) for Cost Explorer functionality.

## Capabilities

### New Capabilities

_(none)_

### Modified Capabilities

- **mcp-cost-explorer**: Replace attachment/configuration requirements with deprecation/removal behavior.
- **app-settings**: Cost Explorer MCP env/YAML keys become deprecated no-ops with warning when enable is requested.

## Impact

- **Code**: `settings.py`, `agent/mcp.py`, `agent/builder.py`, `agent/chat_loop.py`, `api/chat.py`, `agent/runner.py`, `agent/guardrails.py`
- **Docs**: `docs/CONFIGURATION.md`, `docs/MCP.md`, `config/settings.yaml`
- **Tests**: `tests/test_settings.py`, `tests/test_mcp_loading_notification.py`, new tests for deprecation warning and no client attachment
