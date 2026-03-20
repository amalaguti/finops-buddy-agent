## 1. Branch

- [ ] 1.1 **non-`main`** branch.

## 2. Schema and policy

- [ ] 2.1 Finalize event type enum and field names; review with security/compliance.
- [ ] 2.2 Document redaction defaults and optional content flag in **`docs/CONFIGURATION.md`** (and root README pointer if needed).

## 3. Implementation

- [ ] 3.1 Add audit emitter utility (JSON lines); wire to costs/dashboard/context/chat tool hooks.
- [ ] 3.2 Integrate actor resolution with trusted-proxy identity (coordinate with `deploy-aws`).

## 4. Quality

- [ ] 4.1 Ruff, Bandit, pytest (assert JSON schema keys, no token leakage tests).
- [ ] 4.2 `poetry run pytest` and `poetry run pip-audit`.

## 5. Spec sync

- [ ] 5.1 Sync to `openspec/specs/` when complete.
