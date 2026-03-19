## Why

Users need to see which version of FinOps Buddy is running (e.g. when reporting issues or comparing environments). The value should reflect the actual deployed build: package version from `poetry build` plus the exact code revision (commit SHA) when available.

## What Changes

- Add a **backend version endpoint** (e.g. `GET /version`) that returns package version and optional commit SHA. Version comes from installed package metadata; commit comes from an environment variable set at build time (local or Docker).
- Show the **running version in the top nav bar** next to the "FinOps Buddy" label (e.g. `FinOps Buddy  0.1.29 (a1b2c3d)`). The frontend fetches the version from the backend so it always matches the running process.
- Fix **package version lookup** in `finops_buddy/__init__.py`: use the actual package name from `pyproject.toml` (`finops-buddy`) so `__version__` is correct after install.
- Support **Docker builds**: accept a build-arg for commit SHA and set `FINOPS_GIT_SHA` in the image so the backend can expose it.

## Capabilities

### New Capabilities

- `show-version`: The web UI displays the current running version (package version + optional short commit SHA) in the top nav bar. The backend exposes this via a version endpoint; version is from package metadata, commit from env. Same behavior for local runs and Docker.

### Modified Capabilities

- (none)

## Impact

- **Backend API**: New `GET /version` (or `/info`) returning `{ version, commit?, display }`. Reads `__version__` and `FINOPS_GIT_SHA` (or equivalent).
- **Frontend**: One fetch on load (or when header mounts); display the version string next to "FinOps Buddy" in `LayoutSidebar.jsx`.
- **Package**: `__init__.py` uses `version("finops-buddy")` to match `pyproject.toml` name.
- **Docker**: Dockerfile accepts `ARG GIT_SHA`, sets `ENV FINOPS_GIT_SHA`; build invoker passes `--build-arg GIT_SHA=$(git rev-parse --short HEAD)`.
- **Local**: Optional: set `FINOPS_GIT_SHA` in env or a small build step so local runs can show commit too.
