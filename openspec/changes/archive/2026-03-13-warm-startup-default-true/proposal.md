## Why

The `FINOPS_AGENT_WARM_ON_STARTUP` environment variable controls whether the chat agent and profile-to-account mapping are pre-built at API startup. Currently, this defaults to **off**, meaning the first chat request incurs cold-start latency (building the Strands agent, loading tools, caching mappings). Defaulting to **on** improves user experience by eliminating first-request delay, and the setting is undocumented, leaving users unaware it exists.

## What Changes

- **Default to true**: Change `FINOPS_AGENT_WARM_ON_STARTUP` to default to `true` when unset (currently defaults to `false`/empty).
- **Document the setting**: Add documentation in README.md and `config/settings.yaml` template so users know about the warm-up behavior and how to disable it if needed.
- **Add to settings resolution**: Optionally support the warm-up flag in the YAML settings file (e.g. `agent.warm_on_startup`) with env override, following the existing pattern for other agent settings.

## Capabilities

### New Capabilities

_None._

### Modified Capabilities

- `app-settings`: Add requirement for resolving `agent.warm_on_startup` from YAML and environment variable `FINOPS_AGENT_WARM_ON_STARTUP`, with default **true**.

## Impact

- **Code**: `src/finops_buddy/api/app.py` (change default logic), `src/finops_buddy/settings.py` (add warm_on_startup resolution).
- **Docs**: README.md (add configuration section entry), `config/settings.yaml` (add template key).
- **Behavior**: Existing users who relied on implicit off-by-default will now get warm-up unless they explicitly disable it. This is generally beneficial but could slightly increase startup time.
