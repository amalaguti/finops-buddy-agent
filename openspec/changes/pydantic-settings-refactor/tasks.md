## 1. Branch

- [ ] 1.1 **non-`main`** branch.

## 2. Model design

- [ ] 2.1 Inventory all existing getters and env keys; map to Pydantic fields (nested models where helpful).
- [ ] 2.2 Implement YAML loader integration + precedence tests.

## 3. Migration

- [ ] 3.1 Add `pydantic-settings` (or chosen lib) to Poetry; run `poetry lock`.
- [ ] 3.2 Implement `get_settings()` / cached singleton; refactor modules in slices.
- [ ] 3.3 Deprecate redundant `get_*` functions; remove when unused.

## 4. Quality

- [ ] 4.1 `poetry run ruff check .` and `poetry run ruff format .`.
- [ ] 4.2 `poetry run bandit -c pyproject.toml -r src/`.
- [ ] 4.3 Broad pytest updates for settings edge cases; parity tests vs old behavior.
- [ ] 4.4 `poetry run pytest` and `poetry run pip-audit`.

## 5. Documentation

- [ ] 5.1 README + `config/settings.yaml` + strict mode.

## 6. Spec sync

- [ ] 6.1 Merge requirements into canonical `app-settings` / new spec in `openspec/specs/` per workflow.
