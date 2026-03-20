---
inclusion: always
---

# Bandit security scan for OpenSpec changes

When **applying** OpenSpec changes (implementing tasks):

- **Run Bandit** after Ruff lint/format and before pytest:
  - **Scan:** `poetry run bandit -c pyproject.toml -r src/`
- **Fix** any medium or high severity findings as part of the same change.
- Findings MAY be suppressed with `# nosec` comments when they are false positives; include a brief justification.
- When creating **tasks**, place the Bandit step **after** Ruff and **before** pytest tasks.

Implementation is not complete until Bandit passes (no medium+ severity findings) on the changed code.
