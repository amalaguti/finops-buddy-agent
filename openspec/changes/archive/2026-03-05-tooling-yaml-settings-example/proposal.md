# /tooling YAML settings example — Proposal

## Why

Users who want to customize the read-only tool allow-list (`agent.read_only_allowed_tools`) need to know which tools exist and which are currently allowed or blocked. The `/tooling` command already lists tools with allow/block status, but it does not provide a copy-paste-ready YAML example for the settings file. Adding a YAML block with all tools and clear blocked markers helps users build their custom allow-list without hunting through code or docs.

## What Changes

- When the user enters `/tooling`, the CLI SHALL append a YAML example block for `agent.read_only_allowed_tools` that lists all tools shown in the session. Each tool name SHALL appear as a YAML list item; tools that are blocked by the read-only guardrail SHALL have ` (blocked)` appended to the tool name in the YAML (e.g. `create_budget (blocked)`). This makes the example both valid YAML and self-documenting: users can uncomment allowed tools or remove blocked ones to customize.
- In the main tool listing (before the YAML block), blocked tools SHALL show `(blocked)` appended to the tool name (e.g. `create_budget (blocked)`) for consistency and quick scanning.
- The YAML block SHALL be formatted so it can be copied directly into `config/settings.yaml` or the user's settings file under the `agent` section.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- **chat-agent**: The `/tooling` meta-command SHALL display (1) each tool with `(blocked)` appended to the name when the tool is blocked by the read-only guardrail, and (2) a YAML example block for `agent.read_only_allowed_tools` listing all tools with `(blocked)` appended to blocked tool names, ready to copy into the settings file.

## Impact

- **Code**: `src/finops_agent/agent/runner.py` — `_format_tooling_output` (and any helper) to append `(blocked)` to blocked tool names in the listing and to append a YAML example block.
- **Tests**: Update or add tests for the new `/tooling` output format (blocked suffix, YAML block presence and structure).
