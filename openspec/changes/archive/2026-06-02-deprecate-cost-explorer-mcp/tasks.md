## 1. Settings and deprecation

- [x] 1.1 Update `get_cost_explorer_mcp_enabled()` to always return `False` and log a warning when enable is requested via env or YAML
- [x] 1.2 Remove `get_cost_explorer_mcp_command()`, `DEFAULT_COST_EXPLORER_MCP_PACKAGE`, and related command caches/parsers from `settings.py`

## 2. Agent wiring removal

- [x] 2.1 Remove Cost Explorer MCP loading from `api/chat.py`, `agent/chat_loop.py`, and `agent/builder.py`
- [x] 2.2 Remove `create_cost_explorer_mcp_client` from `agent/mcp.py` and `agent/runner.py`
- [x] 2.3 Remove Cost Explorer MCP tool names from `agent/guardrails.py` allow-list

## 3. Documentation

- [x] 3.1 Update `docs/CONFIGURATION.md` and `docs/MCP.md` to document removal and Billing MCP replacement
- [x] 3.2 Update `config/settings.yaml` template (remove or mark Cost Explorer block as deprecated/removed)

## 4. Tests and verification

- [x] 4.1 Update `tests/test_settings.py` for new deprecation behavior; remove command getter tests
- [x] 4.2 Update `tests/test_mcp_loading_notification.py` (no Cost Explorer MCP load step)
- [x] 4.3 Add tests mapping delta spec scenarios (warning on enable request; no attachment)
- [x] 4.4 Run `poetry run ruff check .` and `poetry run ruff format .`
- [x] 4.5 Run `poetry run bandit -c pyproject.toml -r src/`
- [x] 4.6 Run `poetry run pytest`
- [x] 4.7 Run `poetry run pip-audit`
