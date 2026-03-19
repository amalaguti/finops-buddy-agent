# Proposal: AWS Documentation MCP Server integration

## Why

The project roadmap (PROJECT_CONTEXT.md) calls for integrating the **awslabs.aws-documentation-mcp-server** so the chat agent can access up-to-date AWS documentation, search, and recommendations. The agent already uses the remote AWS Knowledge MCP Server and the local Billing MCP Server; adding the open-source **AWS Documentation MCP Server** (run locally via uvx, stdio) gives the agent a second documentation channel with tools such as `read_documentation`, `search_documentation`, and `recommend`, aligning with [AWS MCP servers](https://github.com/awslabs/mcp) and the [AWS Documentation MCP server](https://github.com/awslabs/mcp/tree/main/src/aws-documentation-mcp-server). Users need to see this server and its tools in `/tooling` and `/status` like other MCP servers, and to be able to enable/disable it and override the command.

## What Changes

- **Integrate the AWS Documentation MCP Server** as a local stdio MCP (same pattern as Billing MCP): run via **uvx** (e.g. `awslabs.aws-documentation-mcp-server@latest`) with optional Windows-specific args. The agent will have access to tools such as `read_documentation`, `search_documentation`, and `recommend`.
- **Configuration**: Add enable flag and optional command override (settings and `FINOPS_` env vars). Default: disabled (opt-in) so existing deployments are unchanged; document how to enable and optional env (e.g. `AWS_DOCUMENTATION_PARTITION` for aws vs aws-cn).
- **CLI visibility**: When the Documentation MCP is enabled, it SHALL appear in `/tooling` (by display name, e.g. "AWS Documentation MCP Server") with its tools listed, and in `/status` with readiness, consistent with Knowledge and Billing MCP servers.

## Capabilities

### New Capabilities

- **mcp-aws-documentation**: The agent can use the local AWS Documentation MCP Server (stdio, uvx) for reading and searching AWS documentation and getting recommendations. The CLI exposes this server and its tools in `/tooling` and shows its status in `/status`. Enable/disable and command override are configurable via settings and `FINOPS_`-prefixed environment variables.

### Modified Capabilities

- **chat-agent**: Extend the set of attachable MCP servers so that when the AWS Documentation MCP Server is enabled, it is attached to the agent and listed in `/tooling` and `/status` alongside Knowledge and Billing MCP (no change to existing requirement text; behavior follows current MCP listing and status logic).

## Impact

- **Settings**: New optional keys (e.g. `agent.documentation_mcp_enabled`, `agent.documentation_mcp_command`) and env vars (e.g. `FINOPS_MCP_DOCUMENTATION_ENABLED`, `FINOPS_MCP_DOCUMENTATION_COMMAND`) in `config/settings.yaml` and settings module; cache and reset in `reset_settings_cache()`.
- **Agent build**: New `create_documentation_mcp_client()` (or equivalent) in the agent/runner layer, using stdio transport and `get_documentation_mcp_command()` / `get_documentation_mcp_enabled()`; wire the client into `build_agent()` when enabled. Optional: pass AWS profile/region into subprocess env for consistency (Documentation MCP can use `AWS_DOCUMENTATION_PARTITION`; passing profile/region is optional).
- **Tool listing and status**: Existing `/tooling` and `/status` logic already iterate over tools and MCP clients with `_finops_mcp_server_name`; no spec change required beyond ensuring the new client is built and has the display name set.
- **Docs**: README (or equivalent) updated to document the AWS Documentation MCP Server integration, how to enable it, and the new settings/env vars.
