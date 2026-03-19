## 1. Setup and dependencies

- [x] 1.1 Add FastAPI and uvicorn to pyproject.toml (optional dependency group or main deps); run `poetry lock` and verify install
- [x] 1.2 Create `finops_agent/api/` package with `__init__.py` and a FastAPI app instance (e.g. `app` in `finops_agent/api/app.py` or `main.py`) that can be run with uvicorn

## 2. Profile resolution for API

- [x] 2.1 Implement a dependency or helper that resolves profile from optional query parameter `profile` or header `X-AWS-Profile`; when absent, use `AWS_PROFILE` from env or first profile from `list_profiles()`; reuse existing identity/settings for filtering

## 3. Read-only endpoints

- [x] 3.1 Implement GET /profiles: call `list_profiles()`, return JSON list of profile names; honor excluded/included settings (same as CLI)
- [x] 3.2 Implement GET /context: accept optional profile (query or header), call `get_account_context(profile_name=...)`, return JSON (account_id, arn, role, master/payer); return 4xx/5xx with clear message on credential/session errors
- [x] 3.3 Implement GET /costs: accept optional profile, resolve session, call `get_costs_by_service(session)`, return JSON list of service/cost; return 4xx/5xx with clear message on Cost Explorer or credential errors

## 4. Chat endpoint with streaming

- [x] 4.1 Implement POST /chat: accept body with `message` and optional `messages` (conversation history) and optional `profile`; resolve session and profile; build agent and tools per request (reuse runner/builder logic); run one agent turn
- [x] 4.2 Return response as Server-Sent Events (Content-Type: text/event-stream): if Strands exposes a stream, emit SSE events per chunk; otherwise emit one or more events with the full reply text; support read-only guardrail (same message as CLI when mutating intent detected)
- [x] 4.3 Document SSE event format (e.g. event type and data shape) in code or API docs; optionally include a final event with usage/metadata when available

## 5. Serve subcommand and runnable app

- [x] 5.1 Add `serve` (or `api`) subcommand to CLI that starts the API (e.g. uvicorn run with the FastAPI app); read host/port from settings or env
- [x] 5.2 Ensure the FastAPI app is importable for `uvicorn finops_agent.api:app` (or equivalent) and document in README for advanced users

## 6. Backend configuration

- [x] 6.1 Add optional server (or api) section and getters in settings: host, port, cors_origins; add FINOPS_SERVER_HOST, FINOPS_SERVER_PORT (and optional CORS) env vars; env overrides file; default host 127.0.0.1 and a default port (e.g. 8000)
- [x] 6.2 Add or update config/settings.yaml template with server keys (commented or placeholder values); keep safe to commit
- [x] 6.3 Apply CORS middleware when cors_origins is set; default to same-origin or no CORS when unset

## 7. Documentation

- [x] 7.1 Document backend in README: how to run (`finops serve`), new settings and env vars (FINOPS_SERVER_HOST, FINOPS_SERVER_PORT, CORS), single-user and profile/credentials behavior, and optional uvicorn one-liner

## 8. Quality and tests

- [x] 8.1 Run `poetry run ruff check .` and `poetry run ruff format .`; fix any issues
- [x] 8.2 Add or extend pytest tests for the API: one test per spec scenario where practical (e.g. GET profiles returns filtered list, GET context with profile, GET costs returns data, POST chat streams response, chat respects read-only guardrail, backend uses AWS_PROFILE, server listens on configured port, default bind); place tests in tests/ (e.g. test_api.py or test_backend_api.py); use TestClient or similar for FastAPI
