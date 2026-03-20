---
inclusion: always
---
# Build artifacts before archive

When **archiving an OpenSpec change** (via `/opsx:archive` or equivalent):

## Frontend Build

If the change modified files in `frontend/` or `src/finops_buddy/webui/`:

- **Prompt the user:** "This change touched frontend files. Rebuild the hosted frontend bundle (`cd frontend && npm run build:hosted`)?"
- If yes: run `cd frontend && npm run build:hosted` to regenerate `src/finops_buddy/webui/`
- If no: skip (user may have already built manually)

## Docker Image Rebuild

If the change modified any of these:
- `Dockerfile`
- `docker-compose.yml`
- `pyproject.toml` or `poetry.lock`
- `src/finops_buddy/` Python source files

- **Prompt the user:** "This change may affect the Docker image. Rebuild the image and restart the container?"
- If yes:
  1. Run `docker-compose down` (if container is running)
  2. Run `docker build --build-arg GIT_SHA=$(git rev-parse --short HEAD) -t finops-buddy .` so the web UI nav bar shows version and commit (on Windows PowerShell use the same; or omit `--build-arg GIT_SHA=...` for version-only display)
  3. Run `docker-compose up -d`
- If no: skip (user may not be using Docker)

## Build order (required)

The frontend build writes into `src/finops_buddy/webui/`, which Poetry and Docker both use. So:

1. **Frontend build into webui first:** `cd frontend && npm run build:hosted` → updates `src/finops_buddy/webui/`.
2. **Poetry build second:** `poetry build` packages `src/` (including the built webui) into sdist/wheel. Never run `poetry build` before the frontend build when frontend or webui were changed, or the package will not contain the latest UI.
3. **Docker build last:** `docker build ...` copies `src/` (with the built webui) and runs `poetry install`. Run after frontend (and poetry build if you need a new wheel); the image does not use the local wheel but the same order keeps `src/` up to date.

When doing version bump + build: run frontend build:hosted first if the change touched frontend or webui, then bump version and run `poetry build`, then Docker build if requested.

## Detection

To detect if files were changed, compare the change's `proposal.md` impact section or check git diff against main:
```bash
git diff main --name-only
```

This rule applies **before** the version bump prompt in the archive workflow.
