## Context

The repository already contains an HTTP API (`finops serve`) and a React/Vite frontend. Today, the frontend is served by the Vite dev server and calls the backend over a separate origin, typically `http://localhost:5173` to `http://127.0.0.1:8000`. That split is useful for frontend development, but it is not the runtime model we want for normal app usage or packaging. The goal of this change is to make the FastAPI server the runtime host for both the API and the compiled frontend, while preserving the existing development workflow.

## Goals / Non-Goals

**Goals:**

- Make `finops serve` the single runtime entrypoint for the full local application experience.
- Serve the compiled React app, SPA routes, and bundled static assets from the same FastAPI process that serves the API.
- Keep React and Vite as the frontend authoring and build toolchain.
- Make the hosted frontend use same-origin API calls by default so no separate API base configuration is required in the normal runtime path.
- Package the built frontend assets with the Python app so an installed package can serve the UI without Node.js or a Vite server at runtime.
- Preserve the current backend API contract and development ergonomics.

**Non-Goals:**

- Rewriting the frontend as server-rendered FastAPI templates.
- Eliminating Vite from the developer workflow.
- Replacing React with another UI framework.
- Building a native desktop wrapper or OS-specific installer in this change.
- Changing AWS credential resolution, MCP behavior, or the existing API semantics beyond what is needed for same-host UI serving.

## Decisions

### 1. FastAPI becomes the runtime host, not the frontend build tool

Keep the current React frontend and Vite toolchain. Vite continues to provide development server, asset bundling, and frontend tests. FastAPI becomes responsible only for runtime hosting of the compiled output.

**Why this over replacing Vite entirely?**

- The current frontend is already a working SPA and is only lightly coupled to Vite.
- Rewriting the UI as server templates would be a product and architecture change, not a packaging step.
- Keeping Vite for dev/build gives the project modern frontend ergonomics while removing it from the user runtime path.

### 2. Runtime and development stay intentionally different

Use two modes:

- **Development:** Vite dev server serves the UI; FastAPI serves the API.
- **Runtime / packaged:** FastAPI serves the built UI, static assets, and API from one origin.

This keeps local frontend iteration fast while still delivering the simpler end-user experience.

### 3. Add a dedicated hosted-UI serving layer in the FastAPI app

Extend the FastAPI app to:

- serve the SPA entrypoint for `/`
- serve the SPA entrypoint for known client routes such as `/mcp_tooling_status`
- serve bundled static assets under the generated asset paths
- preserve existing API routes such as `/profiles`, `/context`, `/costs`, `/status`, `/tooling`, and `/chat`
- avoid swallowing API routes, OpenAPI routes, or backend 404s with an over-broad SPA fallback

This is the core runtime decision: the backend remains the system of record for HTTP routing.

### 4. Same-origin becomes the default production API model

Update the frontend API configuration so the hosted build uses same-origin requests by default. Keep an explicit override for development or external hosting scenarios.

**Why this over always requiring `VITE_API_BASE`?**

- In the packaged/runtime model, the frontend and backend are intentionally on the same host and port.
- Same-origin removes unnecessary configuration from the default app experience.
- Retaining an override keeps the frontend flexible for development and advanced deployments.

### 5. Package built frontend assets with the Python distribution

Treat the frontend build output as part of the application package payload. The implementation may copy the built assets into a package-owned directory or otherwise include them as package data, but the outcome must be that an installed package can serve the UI without a separate frontend build step at runtime.

**Alternatives considered:**

- Read assets directly from `frontend/dist` outside the package: simple in the repo, fragile in installed environments.
- Require users to build the frontend after install: defeats the one-install goal.

### 6. Documentation must distinguish runtime hosting from developer tooling

Update the README and architecture docs so they clearly explain:

- how developers run Vite + FastAPI during development
- how users run only `finops serve` in the hosted runtime model
- which parts still depend on local AWS credentials, SSO, and optional MCP subprocess tooling

This avoids the common confusion of thinking “FastAPI replaces Vite” rather than “FastAPI hosts the built frontend at runtime.”

## Risks / Trade-offs

- **[Risk] SPA fallback can interfere with API or docs routes** → Explicitly reserve API and documentation paths before applying frontend fallback behavior, and test both success and 404 cases.
- **[Risk] Frontend assets may be missing from an installed package** → Include package-level verification in the build/test flow and document the asset packaging path clearly.
- **[Trade-off] Development and runtime behavior differ** → Keep docs explicit and preserve `VITE_API_BASE` override so developers can still run the split model intentionally.
- **[Risk] Cache or path assumptions in the built frontend may break under FastAPI hosting** → Validate root path, generated asset paths, and direct navigation to known SPA routes.
- **[Trade-off] Node.js remains a development dependency** → Accept this because it is removed from the end-user runtime path, which is the main goal of the change.

## Migration Plan

- Add hosted frontend serving support to the FastAPI app while preserving existing API endpoints.
- Adjust frontend API configuration to support same-origin by default in the hosted runtime path.
- Integrate frontend build output into the Python package/build process.
- Update docs to describe the new runtime model and the unchanged development model.
- Rollback is straightforward: remove hosted asset serving and package-data integration, and continue using the split frontend/backend runtime only.

## Open Questions

- Should the backend serve a clear diagnostic page or message when the UI bundle is missing, or is a 404 acceptable during development-only API usage?
- Should the hosted runtime expose only the current SPA routes (`/` and `/mcp_tooling_status`) explicitly, or implement a broader SPA fallback strategy for future frontend routes?
- Should the frontend build be produced manually before packaging, or should the Python build flow invoke the frontend build automatically?
