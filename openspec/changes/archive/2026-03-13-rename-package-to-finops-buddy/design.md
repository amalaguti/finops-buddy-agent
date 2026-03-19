## Context

The project's product name is "FinOps Buddy" but the Python package is named `finops_agent`. This inconsistency appears throughout:
- Package directory: `src/finops_agent/`
- PyPI package name: `finops-agent`
- All imports: `from finops_agent import ...`

The CLI command is `finops` and environment variables use `FINOPS_*` prefix - both are appropriate and will remain unchanged (they refer to the FinOps domain, not the package name).

## Goals / Non-Goals

**Goals:**
- Rename internal Python package from `finops_agent` to `finops_buddy`
- Update PyPI package name from `finops-agent` to `finops-buddy`
- Maintain all existing functionality (pure refactoring)
- Keep the rename atomic - complete in one pass to avoid partial states

**Non-Goals:**
- Changing CLI command name (stays `finops`)
- Changing environment variable prefix (stays `FINOPS_*`)
- Renaming workspace folder
- Updating archived OpenSpec changes (historical records)

## Decisions

### 1. Rename directory before updating imports
**Decision**: Rename `src/finops_agent/` → `src/finops_buddy/` first, then update all imports.

**Rationale**: This order allows IDE refactoring tools and grep-replace to work on the new structure. If we update imports first while the directory still has the old name, tests and type checkers will fail during the transition.

**Alternatives considered**:
- Update imports first, then rename: Creates an invalid intermediate state
- Do both simultaneously with script: More complex, harder to verify

### 2. Use search-and-replace for imports
**Decision**: Use systematic search-and-replace for `finops_agent` → `finops_buddy` across all `.py` files in `src/` and `tests/`.

**Rationale**: The rename is mechanical and consistent. All occurrences of `finops_agent` in Python imports should become `finops_buddy`. No selective replacement needed.

**Pattern**:
- `from finops_agent` → `from finops_buddy`
- `import finops_agent` → `import finops_buddy`
- `finops_agent.` → `finops_buddy.` (in strings/paths)

### 3. Update pyproject.toml entries
**Decision**: Update these fields in `pyproject.toml`:
- `name = "finops-agent"` → `name = "finops-buddy"`
- `packages = [{ include = "finops_agent", from = "src" }]` → `packages = [{ include = "finops_buddy", from = "src" }]`
- `include = [{ path = "src/finops_agent/webui/**/*", ... }]` → `include = [{ path = "src/finops_buddy/webui/**/*", ... }]`
- `finops = "finops_agent.cli:main"` → `finops = "finops_buddy.cli:main"`

### 4. Update frontend build output path
**Decision**: Change `package.json` build script from `--outDir ../src/finops_agent/webui` to `--outDir ../src/finops_buddy/webui`.

**Rationale**: The hosted UI runtime expects assets at the new package path.

### 5. Run tests after rename
**Decision**: Run full test suite (`poetry run pytest`) after the rename to verify nothing is broken.

**Rationale**: The rename is mechanical but comprehensive. Running tests confirms all imports resolve correctly.

## Risks / Trade-offs

**[Risk] Missed import reference** → Run `rg "finops_agent"` after rename to catch any stragglers; tests will also catch import errors.

**[Risk] Cached .pyc files with old paths** → Delete `__pycache__` directories before running tests to avoid stale bytecode.

**[Risk] Poetry lock file references old package** → Run `poetry lock` after updating `pyproject.toml` to regenerate lockfile.

**[Trade-off] Breaking change for anyone who installed `finops-agent`** → This is acceptable since the project is pre-release. Users would need to `pip uninstall finops-agent && pip install finops-buddy`.
