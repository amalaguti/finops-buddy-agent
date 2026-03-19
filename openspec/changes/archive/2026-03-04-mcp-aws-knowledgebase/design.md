# Design: AWS Knowledge MCP Server integration

## Context

The chat agent is built with Strands Agents and currently uses only built-in cost tools (`create_cost_tools(session)`). Strands supports MCP via `strands.tools.mcp.MCPClient` and can accept either a list of tool functions or MCP clients. For remote MCP servers using Streamable HTTP, the pattern is `MCPClient(lambda: streamablehttp_client(url))`. The AWS Knowledge MCP Server is a fully managed remote server at `https://knowledge-mcp.global.api.aws`; it does not require AWS authentication and is subject to rate limits. Its tools include `search_documentation`, `read_documentation`, `recommend`, `list_regions`, and `get_regional_availability`. The existing `/tooling` output is produced by `_format_tooling_output(agent, tools_override)` and uses `agent.tools` (or override) and `agent.tool_registry.get_all_tools_config()` to show type, source, and description. The project uses `FINOPS_`-prefixed env vars and `config/settings.yaml` for configuration.

## Goals / Non-Goals

**Goals:**

- Attach the remote AWS Knowledge MCP Server to the chat agent so the agent can call its tools (search_documentation, read_documentation, recommend, list_regions, get_regional_availability).
- When the user runs `/tooling`, show MCP servers by name (e.g. "AWS Knowledge MCP Server") and list the tools they provide, in addition to built-in tools.
- When the agent has used at least one tool from the AWS Knowledge MCP Server to produce a response, inform the user with a short message (e.g. "Consulted AWS Knowledge for this response.").

**Non-Goals:**

- Adding other MCP servers (e.g. billing, cost-explorer) in this change; only AWS Knowledge MCP.
- Changing cost-tool behavior or the rest of the chat loop beyond tool wiring, `/tooling` formatting, and the new notification.
- Implementing retries or custom timeouts for the Knowledge MCP (use library defaults unless necessary).

## Decisions

1. **Use Streamable HTTP and pass MCPClient into Agent**  
   Use `mcp.client.streamable_http.streamablehttp_client` with the Knowledge MCP URL and wrap it in Strands’ `MCPClient`. Pass `Agent(tools=[...cost_tools, knowledge_mcp_client])` so Strands manages the MCP lifecycle. *Rationale*: Matches AWS Knowledge MCP (Streamable HTTP) and Strands’ recommended “managed” integration; no need to run a local process.

2. **Default URL and optional override**  
   Default URL: `https://knowledge-mcp.global.api.aws`. Allow override via settings (e.g. `agent.knowledge_mcp_url`) or env (e.g. `FINOPS_KNOWLEDGE_MCP_URL`) so deployments can point to a different endpoint if needed. *Rationale*: Keeps production URL explicit and testable without hardcoding only in code.

3. **Combine cost tools and MCP in one agent**  
   Build the agent with a single list: `[cost_tools..., knowledge_mcp_client]`. Do not create a separate “knowledge” agent. *Rationale*: One agent can use both cost and documentation tools in the same turn; simpler UX and code.

4. **Extend `/tooling` by detecting MCP clients and listing their tools**  
   In `_format_tooling_output`, when iterating over `agent.tools` (or override), detect Strands `MCPClient` instances (or tools that are clearly from an MCP server). For each MCP client, display a section with a stable server name (e.g. "AWS Knowledge MCP Server") and the list of tools from that server (e.g. via `list_tools_sync()` or equivalent, if available within the current context). Built-in tools continue to be listed as today with Type/Source/description. *Rationale*: Single place for users to see all tools; MCP tools are grouped by server so they are easy to find. *Alternative*: Only list “AWS Knowledge MCP Server” and a count of tools—rejected because the spec asks for tools provided by the MCP server to be listed.

5. **User notification when Knowledge MCP was used**  
   After the agent returns a response, determine if any tool call in that turn was from the AWS Knowledge MCP Server (e.g. by inspecting the result for tool calls and matching tool names to the known Knowledge MCP tool set: `search_documentation`, `read_documentation`, `recommend`, `list_regions`, `get_regional_availability`). If so, print a short line before or after the agent reply (e.g. "Consulted AWS Knowledge for this response."). Implementation can use Strands result metadata (e.g. tool_calls / usage) if exposed; otherwise document the intended behavior and implement as soon as the API allows. *Rationale*: Meets the requirement that the chat agent “inform when contacting the MCP server for information.” *Alternative*: Print the message on every response when MCP is enabled—rejected as noisy and less accurate.

6. **Optional enable/disable for Knowledge MCP**  
   Support a setting (e.g. `agent.knowledge_mcp_enabled`) or env (e.g. `FINOPS_KNOWLEDGE_MCP_ENABLED`) defaulting to true so that deployments can disable the Knowledge MCP without code change. *Rationale*: Avoids surprises in locked-down or air-gapped environments and keeps behavior configurable.

## Risks / Trade-offs

- **Network dependency**: Chat depends on the remote Knowledge MCP being reachable. *Mitigation*: Rely on existing error handling; optional disable flag; consider a short timeout (document in README).
- **Rate limits**: AWS Knowledge MCP is subject to rate limits. *Mitigation*: Document in README; no special retry in this change unless needed later.
- **Tool-call visibility**: If Strands does not expose which tools were called in a turn, the “Consulted AWS Knowledge” message cannot be shown accurately. *Mitigation*: Implement best-effort (e.g. inspect result structure); if not possible, show a generic note when Knowledge MCP is enabled and leave a follow-up task to refine once API is clear.
- **Lifecycle**: MCPClient must be used within a context (or managed by Agent). *Mitigation*: Pass MCPClient directly to Agent so Strands manages lifecycle; ensure chat loop and agent builder keep the same agent (and thus same MCP client) for the session.

## Migration Plan

- No data migration. Deploy: ship code and optional config; if env/settings are unset, use defaults (URL and enabled=true).
- Rollback: set `FINOPS_KNOWLEDGE_MCP_ENABLED=false` (or equivalent) to disable; or revert the change and redeploy.

## Open Questions

- Exact Strands result shape for “tools used this turn” (for the notification line)—to be confirmed during implementation; fallback to generic message or skip if not available.
