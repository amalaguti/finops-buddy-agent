# Proposal: AWS Knowledge MCP Server integration

## Why

The chat agent today uses only built-in cost tools. To improve answer quality and keep guidance aligned with current AWS services, the agent should be able to consult up-to-date AWS documentation, API references, best practices, and regional availability. The **AWS Knowledge MCP Server** is a remote, fully managed MCP server (no local setup) that provides this. Users need visibility: they should see when the agent is consulting AWS Knowledge and which tools are available, including those provided by the MCP server, when they use `/tooling`.

## What Changes

- **Integrate the remote AWS Knowledge MCP Server** into the chat agent. The server URL is `https://knowledge-mcp.global.api.aws` (Streamable HTTP). The agent will have access to tools such as `search_documentation`, `read_documentation`, `recommend`, `list_regions`, and `get_regional_availability`.
- **User notification when contacting the MCP server**: When the agent invokes a tool from the AWS Knowledge MCP Server, the chat CLI will inform the user (e.g. a brief message that AWS Knowledge was consulted for this response).
- **Extend `/tooling`**: The `/tooling` command will list not only built-in tools but also MCP servers by name (e.g. "AWS Knowledge MCP Server") and the tools they provide, so users can see the full tool set including MCP-sourced tools.

## Capabilities

### New Capabilities

- **mcp-aws-knowledge**: The agent can use the remote AWS Knowledge MCP Server for documentation, API references, best practices, and regional availability. The CLI exposes this server and its tools in `/tooling` and informs the user when the agent has used the AWS Knowledge MCP Server for a response.

### Modified Capabilities

- **chat-agent**: Extend the reserved command `/tooling` so that the displayed "internal tooling information" includes MCP servers (by name) and the tools they provide. Add a requirement that when the agent uses a tool from the AWS Knowledge MCP Server, the user is informed (e.g. in the chat output or a short status line).

## Impact

- **Agent build**: Wiring the remote AWS Knowledge MCP Server into the Strands agent (e.g. via Strands MCP client or HTTP transport). May introduce a new module or extend `runner.py` / agent bootstrap.
- **Tool listing**: `/tooling` formatting logic (e.g. `_format_tooling_output` in `runner.py`) and any tool registry or agent API that exposes MCP tools—must include MCP server name and per-server tool list.
- **User notification**: Chat loop or response path—when a response used an AWS Knowledge MCP tool, surface a short informative message (implementation detail in design).
- **Configuration**: Optional settings (e.g. AWS Knowledge MCP URL override, enable/disable) in `config/settings.yaml` and env (e.g. `FINOPS_*`). No new env vars without `FINOPS_` prefix.
- **Docs**: README (or equivalent) updated to mention AWS Knowledge MCP integration, `/tooling` behavior for MCP tools, and the user notification behavior.
