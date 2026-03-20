## 1. Branch

- [ ] 1.1 Work on a **non-`main`** branch (e.g. `feature/agent-session-per-user`).

## 2. Design and API surface

- [ ] 2.1 Finalize session key composition (e.g. `iss` + `sub`) and optional `FINOPS_*` flags for default vs per-user mode.
- [ ] 2.2 Document behavior in **`docs/CONFIGURATION.md`** and `config/settings.yaml` when added.

## 3. Implementation

- [ ] 3.1 Introduce a session registry (get-or-create agent/tool scope per key) replacing global singletons where they affect chat.
- [ ] 3.2 Wire FastAPI dependencies to pass session key into chat/agent build path.
- [ ] 3.3 Add eviction/TTL and metrics/logging for session count (no secrets in logs).

## 4. Quality

- [ ] 4.1 Run `poetry run ruff check .` and `poetry run ruff format .`; fix issues.
- [ ] 4.2 Run `poetry run bandit -c pyproject.toml -r src/`.
- [ ] 4.3 Add pytest covering spec scenarios (concurrent session keys, local default key, eviction policy).
- [ ] 4.4 Run `poetry run pytest`.
- [ ] 4.5 Run `poetry run pip-audit`; address or document findings.

## 5. Spec sync

- [ ] 5.1 After implementation, sync deltas to `openspec/specs/` if required by project workflow.
