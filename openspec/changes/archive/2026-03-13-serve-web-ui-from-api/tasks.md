## 1. Branch and change setup

- [x] 1.1 Create and switch to a non-`main` feature branch for implementation of `serve-web-ui-from-api`.
- [x] 1.2 Review the hosted-web-ui proposal, design, and spec artifacts with the implementation branch checked out before running `/opsx:apply`.

## 2. FastAPI hosted UI runtime

- [x] 2.1 Extend the FastAPI app so `finops serve` can return the compiled SPA entrypoint for `/` and supported frontend routes such as `/mcp_tooling_status`.
- [x] 2.2 Add static asset serving for the compiled frontend bundle while preserving existing API, docs, and OpenAPI routes.
- [x] 2.3 Add runtime behavior for missing frontend assets that is explicit and safe for API-only development usage.

## 3. Frontend runtime configuration

- [x] 3.1 Update the frontend API configuration so the hosted build uses same-origin requests by default while retaining an explicit override for development or advanced deployments.
- [x] 3.2 Verify the frontend works correctly when directly loaded from FastAPI-hosted routes and static asset paths.

## 4. Build and packaging integration

- [x] 4.1 Add a repeatable frontend production build step that generates the bundle used by the hosted runtime.
- [x] 4.2 Include the built frontend assets in the Python package/distribution so an installed app can serve the UI without Vite at runtime.
- [x] 4.3 Verify `finops serve` can run the hosted UI from the packaged asset location, not only from a repo-local `frontend/dist`.

## 5. Documentation and verification

- [x] 5.1 Update `README.md` and `docs/ARCHITECTURE.md` to explain the new runtime model: development uses Vite + FastAPI, while normal app usage runs the full experience through `finops serve`.
- [x] 5.2 Document any build or packaging commands needed to produce the hosted frontend assets and clarify that end users do not need Vite at runtime.
- [x] 5.3 Run `poetry run ruff check .` and `poetry run ruff format .`; fix any issues introduced by the change.
- [x] 5.4 Add or extend pytest tests for backend hosting behavior and route protection, with one test per relevant spec scenario where practical.
- [x] 5.5 Run the relevant frontend verification for hosted mode and the backend test suite to confirm the packaged runtime path works end to end.
