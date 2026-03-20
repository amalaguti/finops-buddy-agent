## 1. Branch

- [ ] 1.1 Use a **non-`main`** branch (e.g. `feature/chat-sse-websocket-resilience`).

## 2. Specification and docs

- [ ] 2.1 Decide **resume semantics** (full vs partial vs none) and document in `docs/` or deployment doc.
- [ ] 2.2 Update README / settings template for any `FINOPS_*` transport flags.

## 3. Frontend

- [ ] 3.1 Implement SSE wrapper with reconnect + backoff; optional `Last-Event-ID` if server supports it.
- [ ] 3.2 Add minimal UX for reconnection state.

## 4. Backend (as needed)

- [ ] 4.1 Implement event ids and resume buffer **or** explicitly return error codes telling client to start a new stream.
- [ ] 4.2 Optional: WebSocket endpoint + parity tests with SSE path.

## 5. Quality

- [ ] 5.1 Frontend: run project lint/build (`npm run build` or equivalent) if TS/React touched.
- [ ] 5.2 `poetry run ruff check .` and `poetry run ruff format .`.
- [ ] 5.3 `poetry run bandit -c pyproject.toml -r src/`.
- [ ] 5.4 Pytest for server event-id behavior; frontend tests if present in repo.
- [ ] 5.5 `poetry run pytest` and `poetry run pip-audit`.

## 6. Spec sync

- [ ] 6.1 Sync deltas to `openspec/specs/` when implementation is complete.
