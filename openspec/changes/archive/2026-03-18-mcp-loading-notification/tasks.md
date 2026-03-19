## 1. Backend: MCP loading logging and progress

- [ ] 1.1 In `api/chat.py`, in `build_agent_and_tools`, when building the tools list (cold path): before each call to `create_*_mcp_client`, log at INFO with the app logger a message like "Loading MCP: <name>…" and, when a progress_callback is provided, call it with event `"mcp_loading"` and message (e.g. "Starting <name> MCP server…"). After each client is created (including when the creator returns None), log "MCP <name> ready" (or "MCP <name> skipped") and, when progress_callback is provided, call it with event `"mcp_loading"` and a "ready" message (e.g. "<name> MCP ready"). Use a consistent short name per MCP (e.g. Billing, Documentation, Cost Explorer, Pricing, Knowledge, Core).
- [ ] 1.2 In `api/app.py`, in `_stream_chat`: when the progress queue returns event `"mcp_loading"` (with the message as the second argument), emit an SSE progress event with `phase: "mcp_loading"` and `message: <that message>` so the UI can show the MCP popup.

## 2. Frontend: MCP loading popup

- [ ] 2.1 Add a popup (modal or toast) component that displays a single message and can be shown/hidden by the parent. When the chat stream receives a progress event with `phase === "mcp_loading"`, show the popup with `data.message`; when the next progress event has phase other than `mcp_loading`, hide the popup. If the first progress event is not `mcp_loading`, do not show the MCP popup for that request. Ensure the popup is dismissible or auto-closes when loading finishes.
- [ ] 2.2 In `ChatView` (or equivalent), wire the SSE progress handler to the new popup: set popup visible and message when phase is `mcp_loading`, clear/hide when phase is not `mcp_loading` or on stream done/error.

## 3. Quality and verification

- [ ] 3.1 Run `poetry run ruff check .` and `poetry run ruff format .`; fix any issues.
- [ ] 3.2 Run `poetry run bandit -c pyproject.toml -r src/`; fix any medium or high severity findings (or document/suppress with justification).
- [ ] 3.3 Add or extend pytest unit tests for the new behavior: at least one test that when building agent and tools with at least one MCP enabled, the logger receives "loading" and "ready" messages in sequence; at least one test that when progress_callback is provided, it is called with mcp_loading-related phase/message (or equivalent) during tool build. Place tests in `tests/` (e.g. `test_chat.py` or `test_api_chat.py`). Name tests after the spec scenarios (e.g. `test_log_before_and_after_each_mcp_client_creation`, `test_stream_sends_mcp_loading_progress_during_cold_build`).
- [ ] 3.4 Run `poetry run pip-audit`; address or document any findings.
