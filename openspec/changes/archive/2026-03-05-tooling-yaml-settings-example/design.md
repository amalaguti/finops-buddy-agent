# /tooling YAML settings example — Design

## Context

The `/tooling` meta-command in `runner.py` calls `_format_tooling_output`, which iterates over agent tools (built-in and MCP), shows each tool's name, type, source, and description, and uses `_is_tool_allowed_by_guardrail` to display `[allowed]` or `[blocked (read-only guardrail)]` per tool. The output does not include a copy-paste-ready YAML example for `agent.read_only_allowed_tools`. Users who want to customize the allow-list must look up tool names elsewhere.

## Goals / Non-Goals

**Goals:**

- Append `(blocked)` to blocked tool names in the main tool listing (e.g. `create_budget (blocked)`) so users can quickly see which tools are blocked.
- Append a YAML example block for `agent.read_only_allowed_tools` that lists all tools shown in the session; blocked tools SHALL have ` (blocked)` appended to their name in the YAML. The block SHALL be valid YAML and ready to copy into the settings file.
- Keep the existing structure (MCP servers, built-in tools, descriptions) intact.

**Non-Goals:**

- Changing how the allow-list is resolved or which tools are blocked.
- Adding interactive editing of the settings file from the chat.

## Decisions

1. **Blocked suffix in main listing**  
   Replace the current `[blocked (read-only guardrail)]` badge with appending ` (blocked)` to the tool name itself (e.g. `• create_budget (blocked)`). This keeps the listing compact and aligns with the YAML format. The existing `[allowed]` / `[blocked]` style can be removed or simplified to avoid redundancy.

2. **YAML block format**  
   After the tool listing, add a section like:
   ```
   ---
   Example for config/settings.yaml (agent.read_only_allowed_tools):
   agent:
     read_only_allowed_tools:
       - get_current_date
       - current_period_costs
       - create_budget (blocked)
       ...
   ```
   All tools from the session (built-in + MCP) SHALL appear. Blocked tools get ` (blocked)` suffix. The block is valid YAML; entries with `(blocked)` are documentation (they do not match real tool names, so they have no effect if left as-is). Users can remove `(blocked)` and uncomment/keep the line to allow that tool.

3. **Tool collection**  
   Reuse the same iteration logic as the main listing: when formatting each tool, collect `(name, allowed)` pairs. After the listing, render the YAML block from that collection. MCP tools come from `list_tools_sync()`; built-in tools from the agent's tool list. Ensure no duplicates and stable ordering (e.g. built-in first, then MCP servers in order).

4. **Placement**  
   The YAML block SHALL appear at the end of the `/tooling` output, after all tools and MCP servers, with a clear separator or heading so users know it is copy-paste material.

## Risks / Trade-offs

- **Long output**: With many MCP servers, the YAML block can be long. Mitigation: no truncation; users can scroll or copy the portion they need.
- **Tool names with special characters**: Tool names are typically alphanumeric with hyphens/underscores. If a tool name contained characters that break YAML (e.g. `:`), we would need to quote it. Current tools do not require this; add quoting only if needed.

## Migration Plan

- No migration. Deploy as a normal release.
- Rollback: revert the change; `/tooling` reverts to previous format.

## Open Questions

- None.
