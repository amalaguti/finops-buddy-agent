## 1. Branch and setup

- [x] 1.1 Create or switch to a feature branch (e.g. `feature/read-only-allowed-tools-in-settings`). Do not implement on `main`.

## 2. Settings and guardrail wiring

- [x] 2.1 In `src/finops_agent/settings.py`, add a getter `get_read_only_allowed_tools()` that returns `frozenset[str]`: read `agent.read_only_allowed_tools` from the loaded YAML; if present and a non-empty list, return `frozenset(that_list)`; otherwise return the default from guardrails (e.g. import and call `get_default_allowed_tools()` from `finops_agent.agent.guardrails` to avoid duplicating the default).
- [x] 2.2 In `src/finops_agent/agent/runner.py`, replace `get_default_allowed_tools()` with `get_read_only_allowed_tools()` when constructing the read-only tool guardrail (e.g. `ReadOnlyToolGuardrail(get_read_only_allowed_tools())`). Ensure the guardrail still receives a frozenset of allowed tool names.

## 3. Config template and docs

- [x] 3.1 Add or update `config/settings.yaml` with an optional `agent.read_only_allowed_tools` entry (commented or with placeholder list) and a short comment that when set to a non-empty list it overrides the default allow-list; when unset or empty, the built-in default is used.
- [x] 3.2 Update README.md (Configuration / Settings section) to document the new setting: key `agent.read_only_allowed_tools`, that it is optional and file-only (no env var), and that it replaces the default allow-list when set to a non-empty list.

## 4. Lint and format

- [x] 4.1 Run `poetry run ruff check .` and `poetry run ruff format .`; fix any reported issues.

## 5. Tests

- [x] 5.1 Add or extend tests in `tests/` for the new behavior: test that `get_read_only_allowed_tools()` returns the default when the key is absent, when it is an empty list, and returns the configured set when `agent.read_only_allowed_tools` is a non-empty list (one test per app-settings scenario: default when key absent, default when empty list, custom list when non-empty).
- [x] 5.2 Add or extend tests for the chat agent / guardrail: when settings provide a custom allow-list, the tool guardrail allows only tools in that list and blocks others (scenario: tool guardrail uses configured allow-list when set).
