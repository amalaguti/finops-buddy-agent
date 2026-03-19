# Tasks: mcp-aws-knowledgebase

## 1. Branch and dependencies

- [x] 1.1 Create a feature branch (e.g. `feature/mcp-aws-knowledgebase`) and do not implement on `main`. Switch to the branch before implementing.
- [x] 1.2 Add MCP streamable HTTP client dependency if not already provided by Strands (e.g. `mcp` with streamable-http transport). Verify `strands.tools.mcp.MCPClient` and `streamablehttp_client` (from `mcp.client.streamable_http` or equivalent) are available for use.

## 2. Configuration

- [x] 2.1 Add or update `config/settings.yaml` with optional keys for AWS Knowledge MCP: URL (default `https://knowledge-mcp.global.api.aws`), enable/disable (default true). Use placeholder/sample values and comment as needed; keep file safe to commit.
- [x] 2.2 Add settings loader support for Knowledge MCP URL and enabled flag (e.g. in `finops_agent.settings` or existing config module). Support override via environment variables `FINOPS_KNOWLEDGE_MCP_URL` and `FINOPS_KNOWLEDGE_MCP_ENABLED` (FINOPS_ prefix required).

## 3. Agent integration

- [x] 3.1 Implement creation of the AWS Knowledge MCP client: use Streamable HTTP with configurable URL (from settings/env), wrap in Strands `MCPClient`. Skip or omit when Knowledge MCP is disabled.
- [x] 3.2 In `build_agent` (or equivalent), combine built-in cost tools with the Knowledge MCP client when enabled: pass `Agent(tools=[...cost_tools, knowledge_mcp_client])` (or list including MCP client) so the agent has both cost and Knowledge MCP tools. Ensure MCP lifecycle is managed (e.g. pass MCPClient directly so Strands manages it).

## 4. /tooling output

- [x] 4.1 Extend `_format_tooling_output` in `runner.py` so that when the agent's tools include an MCP client (e.g. Strands `MCPClient` for AWS Knowledge), the output includes a section for that MCP server by name (e.g. "AWS Knowledge MCP Server") and lists the tools it provides (e.g. via `list_tools_sync()` or equivalent, when available in context). Preserve existing formatting for built-in tools (Type, Source, description).

## 5. User notification when Knowledge MCP is used

- [x] 5.1 After the agent returns a response in the chat loop, determine if any tool call in that turn was from the AWS Knowledge MCP Server (e.g. by inspecting Strands result for tool calls and matching tool names to `search_documentation`, `read_documentation`, `recommend`, `list_regions`, `get_regional_availability`). If so, print a short message (e.g. "Consulted AWS Knowledge for this response.") before or after the agent reply. If the result API does not expose tool usage, implement best-effort or document and add a follow-up; do not block the change.

## 6. Lint and format

- [x] 6.1 Run `poetry run ruff check .` and `poetry run ruff format .`; fix any reported issues.

## 7. Tests

- [x] 7.1 Add or extend pytest tests for mcp-aws-knowledge scenarios: agent can use Knowledge MCP tools when enabled; agent runs without Knowledge MCP when disabled or unreachable; user sees AWS Knowledge MCP Server and its tools in /tooling; user sees notification when agent used AWS Knowledge; no notification when agent did not use it; configuration enable/disable and URL override. Place tests in `tests/test_agent.py` or `tests/test_chat_cli.py` or new `tests/test_mcp_knowledge.py` as appropriate; name tests after the scenario.
- [x] 7.2 Add or extend pytest tests for chat-agent delta scenarios: user enters /tooling and sees MCP servers and their tools; notification shown when agent used AWS Knowledge MCP; no notification when agent did not use it. Reuse or extend existing chat meta-command tests where applicable.

## 8. Documentation

- [x] 8.1 Update README.md Configuration (or Settings and environment) section: document `FINOPS_KNOWLEDGE_MCP_ENABLED`, `FINOPS_KNOWLEDGE_MCP_URL`, and any corresponding `config/settings.yaml` keys; mention that the chat agent can use the remote AWS Knowledge MCP Server and that `/tooling` lists MCP servers and their tools; mention the "Consulted AWS Knowledge" message when the agent used the MCP server.
