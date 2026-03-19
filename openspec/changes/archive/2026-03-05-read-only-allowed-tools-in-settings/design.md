# Read-only allowed tools in settings — Design

## Context

The read-only tool guardrail (see change read-only-agent-guardrails) uses a hardcoded allow-list in `guardrails.py`: `BUILTIN_READ_ONLY_TOOLS`, `MCP_READ_ONLY_TOOL_NAMES`, and `DEFAULT_READ_ONLY_ALLOWED_TOOLS`. The runner constructs the guardrail with `ReadOnlyToolGuardrail(get_default_allowed_tools())`. There is no way to override or extend this list without editing code. The app already loads agent-related settings from YAML under `agent` (e.g. `read_only_guardrail_input_enabled`, `verbose_tool_debug`) and exposes them via `settings.py` getters. This change adds one more optional agent setting and uses it when present.

## Goals / Non-Goals

**Goals:**

- Allow operators to define the read-only tool allow-list in the settings file (YAML list under `agent.read_only_allowed_tools`). When set, the guardrail uses this list; when unset or empty, the application uses the existing built-in default so behavior is backward compatible.
- Keep a single source of truth for the default list in code (guardrails module) for fallback and for documentation; settings only override when explicitly provided.
- No new environment variables; configuration is file-only for this setting.

**Non-Goals:**

- Environment variable override for the allow-list (not required for this change).
- Changing which tools are in the built-in default (that remains in code).
- Validating that configured tool names exist or are safe; operators are responsible for the list they set.

## Decisions

1. **Setting key and shape**  
   Use `agent.read_only_allowed_tools` as a list of strings (tool names). Same format as the existing frozenset in code (e.g. `get_current_date`, `session-sql`, `aws___search_documentation`). If the key is missing or the value is not a list, treat as "use default". Empty list `[]` is treated as "use default" to avoid accidentally allowing no tools.

2. **Where to resolve the list**  
   Add a getter in `settings.py` (e.g. `get_read_only_allowed_tools()`) that: (a) reads `agent.read_only_allowed_tools` from the loaded YAML; (b) if present and a non-empty list, return `frozenset(that_list)`; (c) otherwise return the existing default from guardrails (`get_default_allowed_tools()` or the constant). The guardrails module keeps `get_default_allowed_tools()` and the default constant; the runner (or guardrails) calls the settings getter, which may delegate to the default. This avoids circular imports: settings already imports from guardrails for the default, or we expose the default from guardrails and settings imports it for the fallback.

3. **Guardrail construction**  
   The runner currently does `ReadOnlyToolGuardrail(get_default_allowed_tools())`. Change to `ReadOnlyToolGuardrail(get_read_only_allowed_tools())` where `get_read_only_allowed_tools()` is the new settings getter that returns either the configured list or the default. The guardrail class already accepts an optional `allowed_tools` set; no API change.

4. **Template and docs**  
   Add to `config/settings.yaml` under the agent section a commented example for `read_only_allowed_tools` (e.g. list of a few sample tool names) and document in README that this optional key overrides the default allow-list when set.

## Risks / Trade-offs

- **Operators can lock themselves out**: If the configured list omits a required tool (e.g. `session-sql` or built-in cost tools), the agent may be unable to perform normal read-only operations. Mitigation: document the default list and that overriding replaces it entirely; recommend copying from the default when customizing.
- **No validation of tool names**: We do not check that configured names match real tools. Mitigation: document that names must match exactly what the agent sees (e.g. namespaced MCP names); invalid names simply result in those tools not being callable.

## Migration Plan

- No data migration. Deploy as a normal release.
- Existing deployments: no config change required; they continue using the built-in default.
- Rollback: revert the change; guardrail again uses only the hardcoded default.

## Open Questions

- None.
