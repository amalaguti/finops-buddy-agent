# Web UI for FinOps Agent Chat — Proposal

## Why

The FinOps Agent has a working HTTP API (`finops serve`) with read-only endpoints (profiles, context, costs) and streaming chat (POST /chat, SSE). There is no web UI today; users interact only via the CLI. Adding a professional, good-looking web UI lets users chat with the FinOps agent and optionally view account context and costs in the browser, without requiring the terminal. The backend is already designed for a future React frontend (PROJECT_CONTEXT); this change delivers that frontend.

## What Changes

- Add a **single-page web application** that talks to the existing FastAPI backend. The UI SHALL live in this repo (e.g. `frontend/` or `web/`) and SHALL be buildable and runnable independently (e.g. Vite dev server for development). The UI SHALL look **professional, enterprise-grade, modern, and dynamic**. The application is intended for **desktop use only**; mobile or small-screen support is not required.
- **Three UI variants for validation:** Deliver **three distinct UI interface options** (e.g. different layouts, visual styles, or information architecture) so the product owner can validate and choose the one they prefer before finalizing. Each variant SHALL include the full set of features below; only the look, layout, and interaction patterns differ.
- **Chat (primary):** A chat view where the user can send messages and see the agent’s replies. The UI SHALL call POST /chat with the message and optional conversation history; SHALL consume the SSE stream (events: `message`, `done`, `error`) and display the assistant’s content. Replies SHALL be rendered as markdown (e.g. lists, code, tables). The UI SHALL show a loading state while the agent is responding and SHALL display errors from the `error` event clearly.
- **Profiles:** The UI SHALL show the **profiles the user can work on**: call GET /profiles to populate a profile selector (or list) and SHALL send the selected profile in the chat request body and in requests for context, costs, tooling, and status. The selected profile SHALL be visible and switchable from the UI.
- **MCP servers and status:** The UI SHALL expose **loaded MCP servers and their status**. It SHALL call GET /status (and optionally GET /tooling) and display which MCP servers are loaded and whether they are ready or not, so the user can see connectivity and readiness at a glance.
- **Tools available:** The UI SHALL show **tools available** to the agent (built-in and from MCP). It SHALL call GET /tooling and present the list of tools (and optionally their descriptions) in a dedicated section or panel, so users understand what the agent can do.
- **Costs section:** The UI SHALL include a **dedicated section for costs**: tables, diagrams, or graphics. Data SHALL come from (1) GET /costs (current-month costs by service for the selected profile) and (2) information provided by the agent in chat (e.g. when the agent returns cost breakdowns, comparisons, or summaries). The costs section SHALL support at least tables; it MAY also support charts or diagrams (e.g. bar chart, pie chart) for current-month data or agent-supplied data when applicable.
- **Profile and context:** When a profile is selected, the UI SHALL display account context (GET /context): account ID, role, master/payer indication.
- **Tech stack:** Use **React** with **Vite** for build and dev server, and **Tailwind CSS** for styling, aligned with PROJECT_CONTEXT. Use a markdown renderer (e.g. react-markdown) for assistant messages. No backend code changes beyond any already-supported CORS configuration (FINOPS_CORS_ORIGINS); the API contract remains as-is.
- **Configuration:** The frontend SHALL have a way to configure the API base URL (e.g. environment variable or build-time config) so it can target the running `finops serve` instance (default e.g. http://127.0.0.1:8000). README SHALL document how to run the backend and the UI together (e.g. `finops serve` on port 8000, frontend dev server on port 5173, with CORS set to the frontend origin).

## Capabilities

### New Capabilities

- **web-ui**: The system SHALL provide a web UI that (1) allows the user to chat with the FinOps agent via the existing POST /chat SSE API, with markdown-rendered replies and clear loading and error states; (2) shows the profiles the user can work on (GET /profiles), with profile selection sent to chat, context, costs, tooling, and status; (3) displays account context (GET /context) for the selected profile; (4) shows loaded MCP servers and their status (GET /status) and the list of tools available (GET /tooling); (5) includes a costs section with tables and optionally diagrams or graphics, using GET /costs and agent-provided cost information; and (6) is offered in three distinct UI variants for validation. The UI SHALL be professional, enterprise, modern, and dynamic; SHALL be a React + Vite + Tailwind SPA; SHALL be configurable to point at the backend API base URL; SHALL be documented in the README (run backend, run frontend, CORS); and SHALL be designed for desktop use only (mobile support is out of scope).

### Modified Capabilities

- None. The backend API is unchanged; the UI is a new consumer. Existing specs (backend-api, chat-agent, app-settings) still apply; configuration (e.g. FINOPS_CORS_ORIGINS) is already documented.

## Impact

- **Dependencies:** New frontend dependency set (Node.js, npm/pnpm/yarn for the frontend app; React, Vite, Tailwind, react-markdown, and any SSE/fetch usage). No new Python or backend dependencies.
- **Code:** New frontend directory (e.g. `frontend/`) with React app: three UI variants (distinct layouts/styles for validation), components for chat, profile selector, account context, MCP status panel, tools panel, costs section (tables and optionally charts/diagrams from GET /costs and agent output), and API client for profiles, context, costs, tooling, status, and chat (SSE). No change to `finops_agent` Python packages unless a task explicitly adds a small doc or health check.
- **Configuration:** Frontend API base URL (e.g. `VITE_API_BASE` or similar) and, for local dev, backend CORS already supported via FINOPS_CORS_ORIGINS (or `server.cors_origins` in settings). README update to describe running backend + UI and CORS.
- **Testing:** Frontend can be tested with the project’s preferred approach (e.g. Vitest, React Testing Library, or manual verification against a running backend). No new pytest requirements for backend; optional E2E or contract tests in a follow-up.

## Non-goals (out of scope for this change)

- Backend auth or multi-user support; the UI assumes single-user, same as the API.
- **Mobile or small-screen support;** the UI is designed for desktop execution only.
- Token-level streaming in the UI (backend currently sends one full reply per SSE `message` event; UI can show a single loading state per request).
- Packaging the UI inside the Python app (e.g. serving static files from FastAPI); dev workflow is backend + separate frontend dev server; production deployment strategy (same host vs separate) can be decided later.
