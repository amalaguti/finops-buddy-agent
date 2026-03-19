# Proposal: Core MCP Server as single FinOps MCP

## Why

The project currently wires multiple AWS MCP servers individually (Knowledge, Billing/BCM, Documentation, Cost Explorer, Pricing), each with its own enable flag and command. The [AWS Core MCP Server](https://github.com/awslabs/mcp/tree/main/src/core-mcp-server) provides a single stdio process that proxies several MCP servers based on role-based environment variables (e.g. `finops`, `aws-foundation`, `solutions-architect`). Adopting Core MCP as an option reduces the number of subprocesses for cost-related and documentation/knowledge tooling, gives access to the Core `prompt_understanding` planning tool, and aligns with AWS’s recommended role-based configuration. Users who prefer the current per-server setup can leave Core disabled and keep using the existing MCP toggles.

## What Changes

- **New optional MCP client**: Add the AWS Core MCP Server as an attachable MCP client, run via stdio (e.g. `uvx awslabs.core-mcp-server@latest`), with enable/disable and configurable roles via settings and environment variables.
- **Default roles**: When Core MCP is enabled, support configuring which roles are active; default or recommended set: `finops`, `aws-foundation`, `solutions-architect` (cost, knowledge/docs, solution-architecture tooling).
- **Mutual exclusion with standalone cost MCPs**: When Core MCP is enabled, the agent SHALL NOT attach the standalone Billing, Cost Explorer, or Pricing MCP clients, to avoid duplicate tools. Built-in cost tools SHALL remain disabled when Core MCP is enabled (same behavior as when Billing MCP is enabled).
- **Tooling and status**: `/tooling` and `/status` SHALL indicate that the Core MCP Server is loaded and SHALL indicate which roles are configured (and thus which proxied servers are loaded), so users can see which MCP servers are active due to Core roles.
- **Settings and env**: New YAML keys and `FINOPS_`-prefixed environment variables for Core MCP: enabled flag, optional command override, and role list (e.g. comma-separated or list). Document in README and keep `config/settings.yaml` template updated.
- **No breaking change**: Existing MCP servers (Knowledge, Billing, Documentation, Cost Explorer, Pricing) remain configurable; when Core MCP is disabled, behavior is unchanged. Users opting into Core will set `FINOPS_MCP_BILLING_ENABLED=false`, `FINOPS_MCP_PRICING_ENABLED=false` (and leave Cost Explorer disabled) when using Core.

## Capabilities

### New Capabilities

- `mcp-core-server`: Defines how the FinOps chat agent uses the optional AWS Core MCP Server: enable/disable, role configuration (e.g. finops, aws-foundation, solutions-architect), mutual exclusion with standalone Billing/Cost Explorer/Pricing MCPs, disabling of built-in cost tools when Core is enabled, and exposure of Core and its roles in `/tooling` and `/status`.

### Modified Capabilities

- `app-settings`: Add resolution for Core MCP settings (enabled, command, roles) from YAML and environment variables (`FINOPS_MCP_CORE_*`).
- `chat-agent`: Extend MCP attachment and tool-building logic so that when Core MCP is enabled, the agent attaches the Core client and does not attach Billing, Cost Explorer, or Pricing MCP clients; built-in cost tools are disabled when Core is enabled; `/tooling` and `/status` show Core MCP Server and its configured roles (and thus which proxied servers are loaded).

## Impact

- **Code**: `src/finops_agent/settings.py` (Core MCP getters, caches, env/YAML resolution), `src/finops_agent/agent/runner.py` (create Core MCP client, build_agent logic to skip Billing/Cost Explorer/Pricing when Core enabled, /tooling and /status formatting for Core and roles).
- **Config**: `config/settings.yaml` template (new `agent.core_mcp_*` keys).
- **Docs**: README Configuration section (Core MCP env vars and settings).
- **Tests**: New or extended tests in `tests/test_settings.py`, `tests/test_agent.py` (and optionally `tests/test_chat_cli.py`) for Core enable/disable, role config, mutual exclusion, and /tooling//status display of Core and roles.
- **Dependencies**: No new runtime dependencies; Core MCP is run as an external process (e.g. uvx) like other stdio MCP servers.
