## 1. Branch and discovery

- [x] 1.1 Create a feature branch (e.g. `feature/mcp-billing-cost-management`); do not implement on `main`.
- [x] 1.2 Review AWS MCP docs for Billing and Cost Management and Cost Explorer servers: how to run locally via **uvx** (stdio), and how Strands agents attach MCP tools (command-based server). **Reference:** <https://github.com/awslabs/mcp/tree/main/src/billing-cost-management-mcp-server>.

## 2. Configuration

- [x] 2.1 Add optional MCP-related settings (e.g. enable flag, server URL or command) and FINOPS_ prefixed env vars; load them in settings or agent layer.
- [x] 2.2 Add or update `config/settings.yaml` with MCP-related keys (commented or placeholder); keep safe to commit.
- [x] 2.3 Document MCP configuration and how to run the local MCP servers in README.md.

## 3. MCP server lifecycle (local, uv/uvx)

- [x] 3.1 Support running the Billing and Cost Management and Cost Explorer MCP servers locally via **uvx** (primary): document the uvx command(s) and, if desired, optionally spawn uvx from the CLI when MCP is enabled. Document Docker as an alternative in README per AWS MCP repo.
- [x] 3.2 Document in README: install uv, then how to start the MCP servers (e.g. `uvx awslabs.billing-cost-management-mcp-server@latest`) before or when using `finops chat` with MCP.

## 4. Agent integration

- [x] 4.1 Wire Strands agent to attach MCP server tools when MCP is enabled and configured (use Strands MCP client support).
- [x] 4.2 Ensure the chat agent builds with in-process tools plus MCP tools when MCP is available; only in-process tools when MCP is disabled or unreachable.

## 5. Lint, format, and tests

- [x] 5.1 Run `poetry run ruff check .` and `poetry run ruff format .`; fix any issues.
- [x] 5.2 Add or extend pytest tests for MCP config resolution and for agent building with/without MCP (mock MCP client where needed); one test per spec scenario where practical.
