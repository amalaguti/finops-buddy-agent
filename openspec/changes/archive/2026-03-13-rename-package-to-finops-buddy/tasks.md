## 1. Preparation

- [x] 1.1 Create and switch to a feature branch (e.g., `feature/rename-package-to-finops-buddy`) - do not implement on main
- [x] 1.2 Delete `__pycache__` directories to avoid stale bytecode: `Get-ChildItem -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force`

## 2. Directory Rename

- [x] 2.1 Rename package directory: `src/finops_agent/` → `src/finops_buddy/`

## 3. Update pyproject.toml

- [x] 3.1 Change package name: `name = "finops-agent"` → `name = "finops-buddy"`
- [x] 3.2 Update packages include: `include = "finops_agent"` → `include = "finops_buddy"`
- [x] 3.3 Update webui include path: `src/finops_agent/webui/**/*` → `src/finops_buddy/webui/**/*`
- [x] 3.4 Update CLI entry point: `finops_agent.cli:main` → `finops_buddy.cli:main`
- [x] 3.5 Run `poetry lock` to regenerate lockfile with new package name

## 4. Update Python Imports - Source

- [x] 4.1 Update all imports in `src/finops_buddy/**/*.py`: replace `finops_agent` with `finops_buddy`

## 5. Update Python Imports - Tests

- [x] 5.1 Update all imports in `tests/**/*.py`: replace `finops_agent` with `finops_buddy`
- [x] 5.2 Update `tests/__init__.py` if it references the package

## 6. Update Frontend Build

- [x] 6.1 Update `frontend/package.json` build:hosted script output path: `--outDir ../src/finops_agent/webui` → `--outDir ../src/finops_buddy/webui`

## 7. Update Documentation

- [x] 7.1 Update `README.md`: replace references to `finops_agent` and `finops-agent` with `finops_buddy` and `finops-buddy`
- [x] 7.2 Update `docs/ARCHITECTURE.md`: replace package name references

## 8. Lint and Format

- [x] 8.1 Run `poetry run ruff check .` and fix any issues
- [x] 8.2 Run `poetry run ruff format .` and fix any formatting issues

## 9. Run Tests

- [x] 9.1 Run `poetry run pytest` to verify all imports resolve correctly and tests pass

## 10. Verification

- [x] 10.1 Run `rg "finops_agent" src/ tests/` to verify no straggler references remain in source/tests
- [x] 10.2 Verify CLI still works: `poetry run finops --version`
