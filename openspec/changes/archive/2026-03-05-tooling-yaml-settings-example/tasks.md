## 1. Branch and setup

- [x] 1.1 Create or switch to a feature branch (e.g. `feature/tooling-yaml-settings-example`). Do not implement on `main`.

## 2. /tooling output changes

- [x] 2.1 In `_format_tooling_output` (runner.py), when displaying each tool name, append ` (blocked)` to the name when the tool is blocked by the read-only guardrail (instead of or in addition to the current `[blocked (read-only guardrail)]` badge). Ensure both built-in tools and MCP tools use this format.
- [x] 2.2 In `_format_tooling_output`, collect all tool names (built-in + MCP) with their allow/block status during the listing iteration. After the tool listing, append a YAML example block for `agent.read_only_allowed_tools` that lists all tools; for blocked tools append ` (blocked)` to the name in the YAML. Format the block with a heading (e.g. "Example for config/settings.yaml (agent.read_only_allowed_tools):") and valid YAML structure so it can be copied into the settings file.

## 3. Lint and format

- [x] 3.1 Run `poetry run ruff check .` and `poetry run ruff format .`; fix any reported issues.

## 4. Tests

- [x] 4.1 Add or extend tests for `/tooling` output: verify that blocked tools show `(blocked)` suffix in the listing, and that the YAML example block is present, contains all tools, and blocked tools have `(blocked)` in the YAML. Place tests in `tests/test_chat_cli.py` or `tests/test_agent.py` as appropriate; name tests after the scenarios (e.g. `test_tooling_blocked_tools_show_blocked_suffix`, `test_tooling_displays_yaml_example_for_read_only_allowed_tools`).
