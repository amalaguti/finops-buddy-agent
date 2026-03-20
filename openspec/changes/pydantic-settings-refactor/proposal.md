## Why

`settings.py` has grown into a **large flat collection** of getters and env parsers. That pattern **does not scale** with cloud deployment surface (`FINOPS_*` explosion), makes **validation at startup** hard (failures surface on first lazy access), and lacks **type safety** for IDE/refactor support.

## What Changes

- Introduce a **typed settings model** (e.g. **Pydantic `BaseSettings`** with `FINOPS_` prefix, or equivalent) that **centralizes** env + YAML overlay and **validates** on load.
- **Migration path**: keep thin **backward-compatible** accessors or a single `get_settings()` singleton during transition; deprecate ad-hoc `get_*` triplet pattern over time.
- **Startup validation**: fail fast on invalid combinations (e.g. cloud mode without targets) when configured to **strict** mode.

## Capabilities

### New Capabilities

- `typed-application-settings`: Normative model for loading, validating, and accessing settings.

### Modified Capabilities

- `app-settings`: Requirements updated to describe the typed model as the source of truth; existing scenarios migrate without behavior change for valid configs.

## Impact

- `src/finops_buddy/settings.py` (major refactor), all call sites, **new dependency** (`pydantic-settings` if used), tests for invalid env/YAML.
