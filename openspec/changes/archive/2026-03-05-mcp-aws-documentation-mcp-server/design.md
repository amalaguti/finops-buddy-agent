# Design: AWS Documentation MCP Server integration

## Context

The chat agent already integrates the AWS Knowledge MCP Server (remote, Streamable HTTP) and the AWS Billing and Cost Management MCP Server (local, stdio via uvx). The **AWS Documentation MCP Server** ([awslabs.aws-documentation-mcp-server](https://github.com/awslabs/mcp/tree/main/src/aws-documentation-mcp-server)) is an open-source MCP server that provides `read_documentation`, `search_documentation`, and `recommend` (and `get_available_services` for China). It runs via **stdio** (e.g. `uvx awslabs.aws-documentation-mcp-server@latest`), supports env vars such as `AWS_DOCUMENTATION_PARTITION` (aws | aws-cn) and `FASTMCP_LOG_LEVEL`, and does not require AWS credentials for basic doc access. The existing agent build uses `create_knowledge_mcp_client()` and `create_billing_mcp_client(session)`; `/tooling` and `/status` iterate over agent tools and list any with `_finops_mcp_server_name`. Settings already expose `get_billing_mcp_enabled()`, `get_billing_mcp_command()`, and similar for Knowledge MCP; the same pattern will be used for the Documentation MCP.

## Goals / Non-Goals

**Goals:**

- Attach the AWS Documentation MCP Server to the chat agent when enabled, using stdio transport (uvx subprocess), so the agent can call `read_documentation`, `search_documentation`, and `recommend`.
- Expose enable/disable and optional command override via settings and `FINOPS_`-prefixed environment variables; default disabled (opt-in).
- Ensure the Documentation MCP client appears in `/tooling` (by display name "AWS Documentation MCP Server") with its tools listed, and in `/status` with readiness, reusing existing formatting logic.

**Non-Goals:**

- Changing behavior of the Knowledge or Billing MCP servers.
- Adding retries or custom timeouts for the Documentation MCP beyond library defaults.
- Supporting Documentation MCP–specific user notifications (e.g. "Consulted AWS Documentation") in this change; can be added later if desired.

## Decisions

1. **Use stdio transport and mirror Billing MCP pattern**  
   Use `mcp.StdioServerParameters` and `stdio_client` with command/args from a new `get_documentation_mcp_command()` (default: `uvx awslabs.aws-documentation-mcp-server@latest`, with Windows variant using `--from` and `.exe`). Create `create_documentation_mcp_client(session)` that returns an `MCPClient` with `_finops_mcp_server_name = "AWS Documentation MCP Server"`. *Rationale*: Matches the existing Billing MCP integration and the [AWS Documentation MCP Server](https://github.com/awslabs/mcp/tree/main/src/aws-documentation-mcp-server) stdio-only support.

2. **Default disabled (opt-in)**  
   Default `get_documentation_mcp_enabled()` to `False` so existing deployments are unchanged. Allow override via settings (e.g. `agent.documentation_mcp_enabled`) and env (e.g. `FINOPS_MCP_DOCUMENTATION_ENABLED`). *Rationale*: Avoids extra subprocess and uvx dependency unless the user opts in; consistent with Billing MCP defaulting off.

3. **Command override and env**  
   Support `FINOPS_MCP_DOCUMENTATION_COMMAND` and optional YAML `agent.documentation_mcp_command` (parsed with shlex like Billing). Pass through `AWS_PROFILE` and `AWS_REGION` from the session into the subprocess env when provided, so the Documentation MCP can use them if needed; optionally allow `AWS_DOCUMENTATION_PARTITION` via env (user-set) or settings. *Rationale*: Flexibility for air-gapped or custom installs; alignment with Billing MCP command override.

4. **Wire into build_agent() with other MCPs**  
   In `build_agent()`, when tools are not provided: build cost tools (or omit when Billing MCP enabled), append Knowledge MCP client if enabled, append Billing MCP client if enabled, and append Documentation MCP client if enabled. Do not omit in-process cost tools when only Documentation MCP is enabled (only Billing MCP replaces cost tools). *Rationale*: Documentation MCP is additive (docs + search); cost tools remain unless Billing MCP is used.

5. **Reuse /tooling and /status**  
   No change to `_format_tooling_output` or `_format_mcp_status`; the new client will have `_finops_mcp_server_name` and `list_tools_sync()`, so it will be listed automatically. Optionally extend `_mcp_server_name_for_tool` (and any tool-name → server mapping) so that when the agent uses a tool from the Documentation MCP, the callback can show "(MCP: AWS Documentation MCP Server)" if desired; otherwise leave for a follow-up. *Rationale*: Keeps implementation minimal; tool listing and status are generic over MCP clients.

## Risks / Trade-offs

- **Extra subprocess when enabled**: Another uvx process per chat session. *Mitigation*: Default off; document that uv must be installed when enabling.
- **Tool name collisions**: Documentation MCP tools (`read_documentation`, `search_documentation`) have the same names as Knowledge MCP tools. Strands may prefix or namespace; if not, both servers might expose tools with identical names. *Mitigation*: Rely on Strands/MCP client behavior; if both are enabled, ensure tool names are disambiguated (e.g. by server) so the agent can call the intended one. Document in README.
- **Windows uvx usage**: Same as Billing MCP (use `uv tool run --from <pkg> <pkg>.exe` or equivalent). *Mitigation*: Reuse the same platform detection and default command logic as in `get_billing_mcp_command()`.

## Migration Plan

- No data migration. Deploy: ship code and optional config; if env/settings are unset, Documentation MCP remains disabled.
- Rollback: set `FINOPS_MCP_DOCUMENTATION_ENABLED=false` or revert the change and redeploy.

## Open Questions

- Whether to add a "Consulted AWS Documentation"–style notification when the agent uses a Documentation MCP tool (defer to later if not in scope).
