# MCP Billing and Cost Management — Proposal

## Why

The chat agent today only has in-process cost tools (by service, MoM, WoW, biweekly). It cannot answer questions like "costs per linked account" or "marketplace costs" because those require Cost Explorer (or Billing) queries with different dimensions (LINKED_ACCOUNT, PURCHASE_TYPE for Marketplace). The AWS Billing and Cost Management and Cost Explorer MCP servers (from [awslabs.github.io/mcp](https://awslabs.github.io/mcp)) expose those capabilities as MCP tools. Making these servers available locally and wiring them into the Strands agent will let the agent fulfill user requests for linked-account and marketplace cost analysis without expanding our own tool code for every dimension.

## What Changes

- Run **AWS Billing and Cost Management MCP server** and **Cost Explorer MCP server** **locally** via **uv/uvx** (local process, per [AWS MCP docs](https://github.com/awslabs/mcp/tree/main/src/billing-cost-management-mcp-server)); Docker remains an optional alternative. Servers are reachable by the FinOps agent (e.g. stdio when spawned via uvx).
- **Connect** these MCP servers to the Strands chat agent so the agent can invoke their tools (e.g. cost by linked account, marketplace costs, cost optimization) in addition to existing in-process cost tools.
- Add **configuration** (e.g. FINOPS_ prefixed env or settings) to enable/disable MCP or point to local server endpoints; document in README.
- Keep existing in-process cost tools; MCP tools are **additive**. The agent chooses when to use MCP vs built-in tools.

## Capabilities

### New Capabilities

- **mcp-billing-cost**: The FinOps chat agent SHALL have access to tools from locally run AWS Billing and Cost Management and Cost Explorer MCP servers. The system SHALL support running these MCP servers locally via **uv/uvx** (primary; stdio transport). Docker MAY be documented as an alternative. The system SHALL connect the servers to the Strands agent so the agent can answer queries such as costs by linked account and marketplace costs. Configuration for MCP (enable/disable, server command or URL) SHALL use FINOPS_ prefixed env or app settings.

### Modified Capabilities

- None. Existing chat-agent behavior (in-process cost tools, get_current_date) is unchanged; MCP tools extend the agent.

## Impact

- **Dependencies**: Optional runtime for MCP: **uv** (for `uvx`) to run the AWS Billing and Cost Management and Cost Explorer MCP servers as local processes; Docker is an alternative per AWS docs but not required.
- **Code**: MCP client wiring in the agent layer (Strands MCP integration), optional config loading for MCP endpoints/enable flags.
- **Configuration**: New optional settings or env (e.g. FINOPS_MCP_BILLING_ENABLED, FINOPS_MCP_SERVER_COMMAND or URL override) and updates to config/settings.yaml and README.
- **Testing**: Tests for MCP config resolution and for agent having MCP tools available when enabled (may require mocking MCP client).

## References

- **AWS Billing and Cost Management MCP server** (installation, uv/Docker, tools): <https://github.com/awslabs/mcp/tree/main/src/billing-cost-management-mcp-server>
