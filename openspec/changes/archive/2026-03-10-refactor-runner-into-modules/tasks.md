# Tasks: Refactor runner.py into smaller modules

## 1. MCP module

- [x] 1.1 Create `src/finops_agent/agent/mcp.py` and move all MCP client factory functions (`create_knowledge_mcp_client`, `create_billing_mcp_client`, `create_documentation_mcp_client`, `create_cost_explorer_mcp_client`, `create_pricing_mcp_client`, `create_core_mcp_client`), MCP constants, `_probe_mcp_client_readiness`, `_format_mcp_status`, `_mcp_server_name_for_tool`, `_mcp_server_names_from_tools`, and `_is_tool_allowed_by_guardrail` from `runner.py` into `mcp.py`; fix imports (e.g. settings, boto3) so the module runs standalone.

## 2. Format module

- [x] 2.1 Create `src/finops_agent/agent/format.py` and move `_format_tooling_output`, `_format_credentials_output`, and `_format_context_output` from `runner.py` into `format.py`; add imports from `mcp` (and identity/session as needed) so formatters work; keep `_format_tool_result_for_debug` in builder or move to format if used only by formatters (design: used by VerboseToolDebugHook in builder, so move to builder or keep shared helper in one place—prefer builder for debug hook).

## 3. Builder module

- [x] 3.1 Create `src/finops_agent/agent/builder.py` and move `build_agent`, `_create_finops_callback_handler`, `_VerboseToolDebugHook`, `_tool_source_type`, `_tool_origin`, and `_format_tool_result_for_debug` from `runner.py` into `builder.py`; builder SHALL import from `finops_agent.agent.mcp` and `finops_agent.agent.tools` (and guardrails, settings) so agent construction works without importing `chat_loop` or `format`.

## 4. Chat loop module

- [x] 4.1 Create `src/finops_agent/agent/chat_loop.py` and move `run_chat_loop`, `_build_chat_system_prompt`, `_agent_used_knowledge_mcp`, `_is_rate_limit_error`, and `_cleanup_agent_tools` plus the full interactive loop logic from `runner.py` into `chat_loop.py`; chat_loop SHALL import from `builder`, `format`, and `mcp` as needed.
- [x] 4.2 Remove or isolate ad-hoc debug logging (e.g. `debug-905a6f.log` writes) from the chat loop; prefer removal so the loop stays focused on control flow.

## 5. Runner facade

- [x] 5.1 Replace `runner.py` body with a thin facade: import and re-export `build_agent`, `run_chat_loop`, and any symbols that `test_agent.py` or other callers currently import from `runner` (e.g. `_build_chat_system_prompt`, `_format_mcp_status`, `create_*_mcp_client`, `_format_context_output`, `_format_tooling_output`, `_mcp_server_names_from_tools`, `_mcp_server_name_for_tool`, `_create_finops_callback_handler`); ensure no duplicate logic remains in `runner.py`.

## 6. Package and tests

- [x] 6.1 Update `src/finops_agent/agent/__init__.py` if needed so public API (`run_chat_loop`, `create_cost_tools`) is unchanged (imports from `runner` and `tools` as today).
- [x] 6.2 Update tests: in `tests/test_agent.py` (and any other tests that import internals from `runner`), change imports to the new modules where appropriate (e.g. `_format_mcp_status` from `mcp`, `_build_chat_system_prompt` from `chat_loop`) or keep importing from `runner` if re-exports are used; ensure all tests still pass.

## 7. Lint and tests

- [x] 7.1 Run `poetry run ruff check .` and `poetry run ruff format .`; fix any issues.
- [x] 7.2 Add or extend pytest unit tests for the agent-module-structure spec scenarios: test that `build_agent` and `run_chat_loop` are importable from `runner`, that MCP logic lives in `mcp.py`, that builder is importable without importing chat_loop/format (e.g. import `finops_agent.agent.builder` and assert no chat_loop in sys.modules for that import path if feasible), that format and chat_loop modules exist and are used as specified; place tests in `tests/test_agent.py` or a new `tests/test_agent_modules.py` as appropriate.
