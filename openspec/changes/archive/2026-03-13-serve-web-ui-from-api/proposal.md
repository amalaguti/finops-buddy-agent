## Why

The project already has the pieces of one local application: a Python CLI, a FastAPI backend, and a React web UI. In practice, the web experience still runs as two separate runtime processes, which makes the product feel harder to start, package, and distribute than it needs to be. Making `finops serve` the single runtime host simplifies the user experience and creates a clear path to a one-install application.

## What Changes

- Add a new hosted web UI runtime mode where the existing FastAPI server serves the compiled React frontend, the frontend static assets, and the existing API endpoints from the same origin.
- Keep React and Vite for frontend development and production build generation, but remove Vite from the end-user runtime path.
- Make the hosted frontend use same-origin API requests by default, while still allowing an explicit API base override for development or advanced deployments.
- Include the built frontend assets in the Python application package so an installed app can serve the UI without requiring `npm run dev` or a separate frontend server.
- Update documentation to describe the new runtime model: development remains split (Vite + FastAPI), while normal app usage runs through `finops serve`.

## Capabilities

### New Capabilities

- `hosted-web-ui`: The system SHALL provide a single-host runtime mode in which `finops serve` serves the compiled web UI, bundled frontend assets, and existing backend API from the same FastAPI process.

### Modified Capabilities

- None. Existing `backend-api` requirements remain valid; this change adds a new runtime hosting capability around the current backend and frontend.

## Impact

- **Code:** FastAPI app routing and static file hosting, frontend API base configuration, and packaging/build integration for frontend assets.
- **Runtime:** End users run one server process instead of a separate frontend dev server plus backend API server.
- **Packaging:** Python distribution must include the built frontend bundle so the installed app can serve the UI without Node.js at runtime.
- **Documentation:** README and architecture documentation must distinguish development mode from packaged/runtime mode.
