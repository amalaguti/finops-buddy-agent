## 1. Branch

- [ ] 1.1 **non-`main`** branch (e.g. `feature/mcp-runtime-health-degradation`).

## 2. Config and docs

- [ ] 2.1 Add settings keys + `FINOPS_*` for timeouts, breaker thresholds, cooldown; document in **`docs/CONFIGURATION.md`** and **`config/settings.yaml`**.

## 3. Implementation

- [ ] 3.1 Wrap MCP client calls with timeout and classification.
- [ ] 3.2 Implement per-server circuit breaker state (thread/async safe for FastAPI).
- [ ] 3.3 Integrate with agent builder so degraded servers are skipped or stubbed with clear errors.
- [ ] 3.4 Logging: structured reason codes without leaking subprocess env.

## 4. Quality

- [ ] 4.1 `poetry run ruff check .` and `poetry run ruff format .`.
- [ ] 4.2 `poetry run bandit -c pyproject.toml -r src/`.
- [ ] 4.3 Pytest with fakes: timeout, open circuit, partial degradation.
- [ ] 4.4 `poetry run pytest` and `poetry run pip-audit`.

## 5. Spec sync

- [ ] 5.1 Sync to `openspec/specs/` when done.
