## 1. Settings Resolution

- [x] 1.1 Add `get_agent_warm_on_startup() -> bool` function to `src/finops_buddy/settings.py`: check `FINOPS_AGENT_WARM_ON_STARTUP` env (truthy: `1`, `true`, `yes`; falsy: `0`, `false`, `no`, empty), fall back to YAML `agent.warm_on_startup`, default to `True` when neither is set.
- [x] 1.2 Update `src/finops_buddy/api/app.py` to use `get_agent_warm_on_startup()` instead of inline `os.environ.get(...)` check for warm-up decision.

## 2. Documentation

- [x] 2.1 Update README.md: add `FINOPS_AGENT_WARM_ON_STARTUP` to the Configuration section (default: `true`, purpose: pre-warm chat agent at API startup for faster first request).
- [x] 2.2 Update `config/settings.yaml` template: add `agent.warm_on_startup: true` with comment explaining the setting.

## 3. Quality

- [x] 3.1 Run `poetry run ruff check .` and `poetry run ruff format .`; fix any lint/format issues.
- [x] 3.2 Add pytest tests in `tests/test_settings.py` for `get_agent_warm_on_startup()` covering all scenarios: default true, YAML true, YAML false, env override enable, env override disable, empty env uses YAML.
- [x] 3.3 Run `poetry run pytest tests/test_settings.py -v` to verify all tests pass.
