## 1. Setup

- [x] 1.1 Create feature branch `feature/show-version` (never implement on main)

## 2. Package version fix

- [x] 2.1 In `src/finops_buddy/__init__.py`, use `version("finops-buddy")` (or the actual package name from `pyproject.toml`) instead of `finops-agent` so installed package reports correct version

## 3. Backend version endpoint

- [x] 3.1 Add `GET /version` (or `/info` with version key) in `src/finops_buddy/api/app.py`: return JSON `{ version, commit?, display }`; version from `finops_buddy.__version__`, commit from `os.environ.get("FINOPS_GIT_SHA")`; display is `f"{version} ({commit})"` when commit present else `version`
- [x] 3.2 Document `FINOPS_GIT_SHA` in README (optional env for commit in version response)

## 4. Frontend nav bar

- [x] 4.1 In `frontend/src/api/client.js`, add `getVersion()` that fetches `GET /version` and returns the response
- [x] 4.2 In `frontend/src/layouts/LayoutSidebar.jsx`, fetch version on mount (or via a small context), and render the `display` value next to "FinOps Buddy" in the header (e.g. muted span); handle loading and errors without blocking the UI

## 5. Docker

- [x] 5.1 In `Dockerfile`, add `ARG GIT_SHA` and `ENV FINOPS_GIT_SHA=${GIT_SHA}` so the container can expose commit when built with `--build-arg GIT_SHA=$(git rev-parse --short HEAD)`
- [x] 5.2 In README (or Docker section), note optional `docker build --build-arg GIT_SHA=...` for version display with commit

## 6. Quality and tests

- [x] 6.1 Add pytest test for version endpoint: returns 200, JSON has `version` and `display`; when `FINOPS_GIT_SHA` is set (mock env), response includes `commit` and display contains it
- [x] 6.2 Run `poetry run ruff check .` and `poetry run ruff format .`; fix any issues
