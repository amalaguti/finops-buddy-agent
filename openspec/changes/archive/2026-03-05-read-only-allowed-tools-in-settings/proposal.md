# Read-only allowed tools in settings — Proposal

## Why

After the read-only-agent-guardrails change, the list of tools the agent is allowed to run is hardcoded in Python (`guardrails.py`: `BUILTIN_READ_ONLY_TOOLS`, `MCP_READ_ONLY_TOOL_NAMES`). Operators cannot add or remove allowed tools (e.g. for custom MCPs or to temporarily restrict tools) without changing code. Moving the allowed-tools list to the app settings file makes it configurable and keeps the codebase free of deploy-time list edits.

## What Changes

- Add a new optional setting under `agent`: **read-only allowed tools** (YAML list of tool names). When present, the read-only tool guardrail uses this list instead of the built-in default.
- When the setting is absent or empty, behavior is unchanged: use the current default (built-in FinOps tools + known MCP read-only tool names) so existing deployments are unaffected.
- Implement a settings reader (e.g. in `settings.py`) that returns the resolved allow-list (from YAML or default), and have the guardrail and runner use it instead of the hardcoded default.
- No new environment variables: configuration is via the existing settings file only.
- Update `config/settings.yaml` template with the new key and document it in README.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- **app-settings**: New optional key `agent.read_only_allowed_tools` (list of strings). When set, it defines the read-only tool allow-list; when unset, the application uses the built-in default.
- **chat-agent**: The read-only tool guardrail obtains the allow-list from settings (via the new reader). Behavior is unchanged when the new setting is not set.

## Impact

- **Code**: `src/finops_agent/agent/guardrails.py` (keep default constant for fallback; add or use settings-backed resolution), `src/finops_agent/settings.py` (new getter for allowed tools), `src/finops_agent/agent/runner.py` (use settings-backed allow-list when constructing the guardrail).
- **Config**: `config/settings.yaml` gains an optional `agent.read_only_allowed_tools` template entry.
- **Docs**: README configuration section updated to describe the new setting.
- **Tests**: New or updated tests for the settings getter and for guardrail behavior when the setting is set vs unset.
