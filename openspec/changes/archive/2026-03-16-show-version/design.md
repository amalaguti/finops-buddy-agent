## Context

The app has no version endpoint; the frontend has no way to show "what is running." Version should combine the Poetry package version (from `poetry build`) with the git commit SHA when available, for both local and Docker deployments.

## Goals / Non-Goals

**Goals:**

- Backend exposes version + optional commit via a single endpoint.
- Top nav bar shows "FinOps Buddy" plus the running version (e.g. `0.1.29 (a1b2c3d)`).
- Same mechanism for local and Docker; commit SHA injected at build time via env.

**Non-Goals:**

- Version in CLI only (CLI already has `--version`; this change is for the web UI and API).
- Storing version in the frontend bundle at build time (backend is source of truth for "what is running").

## Decisions

### 1. Source of version and commit

- **Version:** From installed package metadata via `importlib.metadata.version("finops-buddy")` in `finops_buddy/__init__.py`. Fix existing lookup to use package name `finops-buddy` (not `finops-agent`).
- **Commit:** From environment variable `FINOPS_GIT_SHA` (short SHA, e.g. 7 chars). Set at build time: locally via env or script; in Docker via build-arg and `ENV FINOPS_GIT_SHA=$GIT_SHA` in Dockerfile. If unset, backend returns no commit and frontend shows only version (e.g. `0.1.29`).

### 2. API shape

- **Endpoint:** `GET /version` (or `/info` with a `version` key). Returns JSON: `{ "version": "0.1.29", "commit": "a1b2c3d" | null, "display": "0.1.29 (a1b2c3d)" }`. When `commit` is missing, `display` is just `version`.
- **No auth:** Read-only, safe to expose.

### 3. Frontend

- **When:** Fetch version once when the app/layout loads (e.g. in `LayoutSidebar` or a small provider). Cache in state or context to avoid repeated calls.
- **Where:** In the top nav bar, next to the "FinOps Buddy" heading (e.g. `<h1>FinOps Buddy</h1> <span className="...">0.1.29 (a1b2c3d)</span>`). Style as secondary/muted so it doesn’t compete with the title.
- **Fallback:** If the request fails, show nothing or "—" for version; do not block the UI.

### 4. Docker

- **Build-arg:** `ARG GIT_SHA` in Dockerfile. Default empty.
- **Env:** `ENV FINOPS_GIT_SHA=${GIT_SHA}` so the running process can read it. Build with: `docker build --build-arg GIT_SHA=$(git rev-parse --short HEAD) ...`.
- **docker-compose:** Can pass build-arg from compose if desired; otherwise document the flag for manual builds.
