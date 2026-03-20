---
inclusion: always
---

# Ruff lint and format for OpenSpec changes

When **applying** OpenSpec changes (implementing tasks):

- **Run Ruff** before running pytest (Ruff first, then tests):
  - **Lint:** `poetry run ruff check .`
  - **Format:** `poetry run ruff format .` (or `poetry run ruff format --check .` to only verify; then fix if needed)
- **Fix** any Ruff-reported issues (lint violations or format changes) as part of the same change.
- When creating **tasks**, place the Ruff step **before** the pytest tasks: "Run `poetry run ruff check .` and `poetry run ruff format .`; fix any issues."

Implementation is not complete until Ruff passes on the changed code.
