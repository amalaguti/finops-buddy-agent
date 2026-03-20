## 1. Branch

- [ ] 1.1 **non-`main`** branch.

## 2. Research

- [ ] 2.1 Confirm AWS **minimum AssumeRole duration** and org policy; pick probe strategy (AssumeRole vs simulation API).

## 3. Implementation

- [ ] 3.1 Add validation runner invoked from FastAPI lifespan or dedicated startup hook.
- [ ] 3.2 Implement strict/warn flags + rate limiting.
- [ ] 3.3 Metrics/logging for pass/fail counts.

## 4. Quality

- [ ] 4.1 Ruff, Bandit, pytest with mocked STS (success, AccessDenied, throttle).
- [ ] 4.2 `poetry run pytest` and `poetry run pip-audit`.

## 5. Documentation

- [ ] 5.1 README + `config/settings.yaml` + operator runbook snippet.

## 6. Spec sync

- [ ] 6.1 Sync to `openspec/specs/` when complete.
