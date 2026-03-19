## 1. Branch and discovery

- [x] 1.1 Create a feature branch (e.g. `feature/mcp-aws-documentation-mcp-server`); do not implement on `main`.
- [x] 1.2 Review AWS Documentation MCP Server docs: run locally via **uvx** (stdio), default package `awslabs.aws-documentation-mcp-server@latest`, tools `read_documentation`, `search_documentation`, `recommend`. **Reference:** [aws-documentation-mcp-server](https://github.com/awslabs/mcp/tree/main/src/aws-documentation-mcp-server).

## 2. Configuration

- [x] 2.1 In the settings module, add support for Documentation MCP: enable flag (default False) and optional command override; use `FINOPS_MCP_DOCUMENTATION_ENABLED` and `FINOPS_MCP_DOCUMENTATION_COMMAND`; YAML keys e.g. `agent.documentation_mcp_enabled`, `agent.documentation_mcp_command`; include in `reset_settings_cache()`.
- [x] 2.2 Add default package constant and `get_documentation_mcp_enabled()`, `get_documentation_mcp_command()` with platform-specific default (Windows: uv with `--from` and `.exe`; else uvx with package), mirroring Billing MCP pattern.
- [x] 2.3 Add or update `config/settings.yaml` with Documentation MCP keys (e.g. `documentation_mcp_enabled`, `documentation_mcp_command`) as template with commented or placeholder values; keep safe to commit.
- [x] 2.4 Document Documentation MCP configuration and new env vars in README.md (Configuration / Settings and environment section).

## 3. Agent integration

- [x] 3.1 In the agent/runner layer, add `create_documentation_mcp_client(session)` that returns an MCP client (stdio, `StdioServerParameters` + `stdio_client`) when enabled, with `_finops_mcp_server_name = "AWS Documentation MCP Server"`; pass session profile/region into subprocess env when provided; return None when disabled.
- [x] 3.2 In `build_agent()`, when building tools list, append the Documentation MCP client when enabled (after Knowledge and Billing MCP clients); do not omit in-process cost tools when only Documentation MCP is enabled.
- [x] 3.3 Optionally extend `_mcp_server_name_for_tool` (and callback) so that tool invocations from the Documentation MCP show "(MCP: AWS Documentation MCP Server)" in the chat callback; ensure `/tooling` and `/status` list the Documentation MCP server and its tools when present (existing logic should cover this if client has `_finops_mcp_server_name` and `list_tools_sync`).

## 4. Lint, format, and tests

- [x] 4.1 Run `poetry run ruff check .` and `poetry run ruff format .`; fix any issues.
- [x] 4.2 Add or extend pytest tests: settings (get_documentation_mcp_enabled default False, override from env/YAML; get_documentation_mcp_command default and override; reset_settings_cache clears Documentation MCP caches); agent (create_documentation_mcp_client returns None when disabled, build_agent includes Documentation MCP client when enabled); chat CLI (/tooling and /status show Documentation MCP when enabled). One test per spec scenario where practical; name tests after scenarios.
