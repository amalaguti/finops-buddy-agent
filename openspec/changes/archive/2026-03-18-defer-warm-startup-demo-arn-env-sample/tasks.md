# Tasks: Defer warm startup, demo ARN mask, env sample

## 1. Branch and setup

- [ ] 1.1 Ensure you are not on `main`. Create or switch to a feature branch (e.g. `feature/defer-warm-startup-demo-arn-env-sample`) before implementing.

## 2. Defer agent warm-up to lifespan

- [ ] 2.1 In `src/finops_buddy/api/app.py`, add an `@asynccontextmanager` lifespan function that, before `yield`, calls `warm_chat_agent_on_startup()` when `get_agent_warm_on_startup()` is true.
- [ ] 2.2 Pass the lifespan to `FastAPI(lifespan=...)` and remove the module-level call to `warm_chat_agent_on_startup()` (and the surrounding `if get_agent_warm_on_startup():` block).

## 3. Demo ARN session name masking

- [ ] 3.1 In `src/finops_buddy/api/demo.py`, add a constant for the placeholder session name (e.g. `DEMO_MASK_ARN_SESSION_NAME = "john.doe@finops.buddy"`).
- [ ] 3.2 Implement `_mask_arn_value(arn, id_mapping)` that applies existing account-ID masking to the ARN string, then for strings containing `assumed-role/` or `:assumed-role/`, replaces the segment after the last `/` with the placeholder.
- [ ] 3.3 In `_mask_dict`, when the key is `"arn"` and the value is a string, set `result["arn"] = _mask_arn_value(value, id_mapping)`.

## 4. Env sample and docs

- [ ] 4.1 Add `env.local.sample` at the project root (no leading dot) with all supported `FINOPS_*` environment variables and placeholder/sample values; no real secrets.
- [ ] 4.2 Update README.md (or Configuration section) to describe `env.local.sample` and how to copy it to `.env.local` for local overrides.

## 5. Tests and quality

- [ ] 5.1 Run `poetry run ruff check .` and `poetry run ruff format .`; fix any issues.
- [ ] 5.2 Add or extend pytest: in `tests/test_demo.py`, add a test that when `mask_response_data` is called with an `arn` containing an assumed-role ARN with a session name, the result ends with the placeholder and does not contain the original session name (e.g. email).
- [ ] 5.3 Run `poetry run pytest tests/test_demo.py -v` (and full suite if desired) to confirm no hang and all tests pass.
