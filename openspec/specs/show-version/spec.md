# Capability: show-version

## Requirements

### Requirement: Backend exposes running version

The HTTP API SHALL provide a read-only endpoint (e.g. `GET /version`) that returns the current running version and, when available, the git commit SHA. Version SHALL come from the installed package metadata (e.g. `finops_buddy.__version__`). Commit SHALL come from an environment variable (e.g. `FINOPS_GIT_SHA`) set at build time. The response SHALL include a `display` string suitable for showing in the UI (e.g. `"0.1.29 (a1b2c3d)"` or `"0.1.29"` when commit is absent).

#### Scenario: Version endpoint returns package version and commit

- **WHEN** the backend is run with package version `0.1.29` and `FINOPS_GIT_SHA` set to `a1b2c3d`
- **THEN** `GET /version` returns JSON with `version`, `commit`, and `display` (e.g. `"0.1.29 (a1b2c3d)"`)

#### Scenario: Version endpoint returns only version when commit is unset

- **WHEN** the backend is run and `FINOPS_GIT_SHA` is not set
- **THEN** `GET /version` returns JSON with `version` and `display` equal to the package version; `commit` is null or omitted

### Requirement: Package version is resolved from correct package name

The package SHALL expose `__version__` in `finops_buddy/__init__.py` using the same package name as declared in `pyproject.toml` (e.g. `finops-buddy`) so that after `poetry install` or install from wheel/sdist the version matches the built artifact.

#### Scenario: Installed package reports correct version

- **WHEN** the project is installed via `poetry install` or from a built wheel with version `0.1.29`
- **THEN** `finops_buddy.__version__` equals `"0.1.29"` (or the built version)

### Requirement: Web UI shows version in top nav bar

The web UI SHALL display the running version next to the "FinOps Buddy" label in the top navigation bar. The displayed value SHALL be obtained from the backend version endpoint (e.g. the `display` field) so it always reflects the running process. The version SHALL be shown for both local runs and when the UI is served from the same backend (e.g. hosted or Docker).

#### Scenario: Nav bar shows version on load

- **WHEN** the user opens the FinOps Buddy web UI and the backend responds to `GET /version` with `{ "display": "0.1.29 (a1b2c3d)" }`
- **THEN** the top nav bar shows "FinOps Buddy" and the version string (e.g. `0.1.29 (a1b2c3d)`)

#### Scenario: Nav bar degrades gracefully when version endpoint fails

- **WHEN** the version endpoint is unavailable or returns an error
- **THEN** the nav bar still shows "FinOps Buddy" and does not block the rest of the UI; version may be omitted or shown as a placeholder

### Requirement: Docker image can expose commit SHA

The Docker build SHALL support an optional build-arg (e.g. `GIT_SHA`) that is set as an environment variable (e.g. `FINOPS_GIT_SHA`) in the image so the backend can include the commit in the version response. When the image is built with `--build-arg GIT_SHA=$(git rev-parse --short HEAD)`, the running container SHALL report that commit via the version endpoint.

#### Scenario: Docker container reports version and commit

- **WHEN** the image is built with `GIT_SHA` build-arg set to a short commit SHA and the backend runs in the container
- **THEN** `GET /version` from that container returns the package version and the given commit in the response
