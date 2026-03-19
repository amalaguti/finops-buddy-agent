## Why

The project is called "FinOps Buddy" but the internal Python package is named `finops_agent`. This creates a disconnect between the product identity and the codebase. Renaming the package to `finops_buddy` aligns the code with the product name and improves consistency across documentation, imports, and developer experience.

## What Changes

- Rename Python package from `finops_agent` to `finops_buddy` (directory `src/finops_agent/` → `src/finops_buddy/`)
- Update `pyproject.toml` package name from `finops-agent` to `finops-buddy`
- Update all internal Python imports from `finops_agent.*` to `finops_buddy.*`
- Update test imports to reference `finops_buddy`
- Update documentation references (README, ARCHITECTURE.md)
- Update frontend build script output path (`src/finops_agent/webui` → `src/finops_buddy/webui`)
- CLI command remains `finops` (no change to user-facing CLI)
- Environment variables remain `FINOPS_*` (no change - these refer to the FinOps domain)

## Capabilities

### New Capabilities

(None - this is a refactoring change, not a feature addition)

### Modified Capabilities

(None - no spec-level behavior changes, only internal naming)

## Impact

- **Source code**: All `.py` files with `finops_agent` imports (~20+ source files, ~15+ test files)
- **Build config**: `pyproject.toml` package definition and include paths
- **Frontend**: `package.json` build script output directory
- **Documentation**: README.md, docs/ARCHITECTURE.md
- **Archived OpenSpec changes**: Historical references remain unchanged (they document what was true at the time)
- **No breaking changes for end users**: CLI command (`finops`) and env vars (`FINOPS_*`) stay the same
