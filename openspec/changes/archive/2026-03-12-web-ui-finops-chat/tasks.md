# Web UI for FinOps Agent Chat — Tasks

The UI is intended for **desktop use only**; mobile or small-screen support is out of scope.

## 1. Branch and documentation

- [x] 1.1 Create a feature branch (e.g. `feature/web-ui-finops-chat`); do not implement on `main`.
- [x] 1.2 **Architecture diagram and explanation:** Add a proper diagram and written explanation of the whole system architecture to the project docs. Include: (1) **Diagram**: ASCII or image showing CLI, backend API (`finops serve`), and web UI (Vite dev server / SPA); how the browser talks to the frontend origin and the API origin; where credentials and profile flow (env, settings, API request). (2) **Explanation**: Short prose describing each component (CLI, FastAPI backend, React/Vite frontend), their roles, how they share the same core (`finops_agent`), and the dev vs production picture (two processes in dev: Vite + finops serve; CORS for cross-origin API calls). Place the diagram and explanation in a doc that lives in the repo (e.g. `docs/ARCHITECTURE.md` or a new section in README or in `openspec/docs/`), and ensure it is referenced or linked from README so users and contributors can find it.

## 2. Frontend scaffold

- [x] 2.1 Create the frontend app (e.g. `frontend/` at repo root) with React, Vite, and Tailwind CSS; add a minimal entry point and ensure it runs with the Vite dev server (e.g. `npm run dev` → http://localhost:5173).
- [x] 2.2 Add configuration for the API base URL (e.g. `VITE_API_BASE` or similar) so the app can target the running `finops serve` instance (default e.g. http://127.0.0.1:8000).

## 3. Three UI variants

- [x] 3.1 Implement **three distinct UI interface options** (e.g. different layouts, visual styles, or information architecture) so the product owner can validate and choose a preferred one. Each variant SHALL be professional, enterprise-looking, modern, and dynamic; SHALL include the full feature set (chat, profiles, context, MCP status, tools, costs section). Variants may differ by: layout (e.g. sidebar vs top nav, chat-centric vs dashboard-centric), theme (e.g. light/dark, accent colors), or panel organization. Deliver all three in the same app (e.g. route or theme switcher) or as separate entry points / builds for easy comparison.

## 4. Chat UI

- [x] 4.1 Implement the chat view: message list (user + assistant), input field, and send action. On send, call POST /chat with the message and optional conversation history; consume the SSE stream (events: `message`, `done`, `error`) and display the assistant’s content; show loading state while waiting for the response; display errors from the `error` event clearly.
- [x] 4.2 Render assistant replies as markdown (e.g. react-markdown) so lists, code, and tables display properly.

## 5. Profiles, context, MCP status, and tools

- [x] 5.1 **Profiles:** Call GET /profiles to populate a profile selector (dropdown or list); send the selected profile in the POST /chat body and in requests for context, costs, tooling, and status. Make the selected profile visible and switchable.
- [x] 5.2 **Account context:** When a profile is selected, display account context (GET /context): account ID, role, master/payer indication.
- [x] 5.3 **MCP servers and status:** Call GET /status and display loaded MCP servers and their readiness (ready / not ready) in a dedicated section or panel.
- [x] 5.4 **Tools available:** Call GET /tooling and display the list of tools available to the agent (built-in and MCP), with optional short descriptions, in a dedicated section or panel.

## 6. Costs section

- [x] 6.1 Implement a **costs section** that shows cost data in **tables**; optionally support **diagrams or graphics** (e.g. bar chart, pie chart). Data sources: (1) GET /costs (current-month costs by service for the selected profile); (2) cost-related information provided by the agent in chat (e.g. when the agent returns breakdowns, comparisons, or summaries that can be rendered as a table or chart). Ensure the section is visible and usable in all three UI variants.

## 7. README and config

- [x] 7.1 Update README.md: how to run the backend (`finops serve`) and the UI (e.g. `cd frontend && npm run dev`); set CORS (FINOPS_CORS_ORIGINS or `server.cors_origins` in settings) to the frontend origin (e.g. http://localhost:5173); link to or summarize the architecture doc (diagram and explanation); how to switch between or compare the three UI variants if applicable.
- [x] 7.2 Document the frontend API base URL configuration (e.g. `VITE_API_BASE`) in README or frontend README so users know how to point the UI at a different backend.

## 8. Lint, format, and tests

- [x] 8.1 Run `poetry run ruff check .` and `poetry run ruff format .` for any backend or shared config touched; fix issues. For the frontend, run the project’s chosen lint/format (e.g. ESLint, Prettier) if applicable.
- [x] 8.2 Add or extend tests as agreed for the change (e.g. frontend unit tests with Vitest/React Testing Library, or manual verification against a running backend); no new pytest backend tests required unless the change modifies backend code.
