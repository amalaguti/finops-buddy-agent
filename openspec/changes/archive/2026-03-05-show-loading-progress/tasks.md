## 1. Branch and setup

- [x] 1.1 Create feature branch `feature/show-loading-progress` (or switch if on main); do not implement on main

## 2. Progress callback and runner changes

- [x] 2.1 Add a `progress` parameter (callable `(msg: str) -> None`) to `run_chat_loop` in `src/finops_agent/agent/runner.py`; default to `lambda m: print(m, file=sys.stderr, flush=True)`
- [x] 2.2 Emit progress messages in `run_chat_loop` before each major step: resolving credentials, creating cost tools, loading each MCP client (Knowledge, Billing, Documentation, Cost Explorer, Pricing), building agent; end with a "Ready." or equivalent message
- [x] 2.3 Ensure `build_agent` can receive and use a progress callback when called from `run_chat_loop` (or keep progress calls in `run_chat_loop` only if that is sufficient)

## 3. CLI integration

- [x] 3.1 Add `--quiet` (and optionally `-q`) to the chat subparser in `src/finops_agent/cli.py`
- [x] 3.2 Update `cmd_chat` to accept `quiet` (or full args); when `--quiet` is set, pass a no-op progress callback (`lambda m: None`) to `run_chat_loop`; update the chat branch in `main()` to pass `quiet` from parsed args

## 4. Quality and tests

- [x] 4.1 Run `poetry run ruff check .` and `poetry run ruff format .`; fix any issues
- [x] 4.2 Add pytest tests for startup progress: `test_progress_shown_during_chat_startup`, `test_progress_includes_mcp_server_names`, `test_quiet_mode_suppresses_startup_progress` in `tests/test_agent_runner.py` (or appropriate test module)

## 5. Documentation

- [x] 5.1 Document the `--quiet` flag for the chat command in README.md (e.g. under CLI usage or chat section)
