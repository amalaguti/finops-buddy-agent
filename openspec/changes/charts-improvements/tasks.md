## 1. Branch and implementation

- [ ] 1.1 Create and switch to a non-`main` branch (e.g. `feature/charts-improvements`) before implementing; do not apply this change on `main`.

- [ ] 1.2 In `src/finops_buddy/agent/chart_tools.py`, apply matplotlib **stylesheet + rcParams** inside `_render_chart` after `Agg` backend selection: set default **figsize**, **savefig DPI** (≥120), and **tight save** with padding; use a named built-in style with a **safe fallback** if the style is missing on the runtime.

- [ ] 1.3 For **bar** charts only, **sort** `(label, value)` pairs by value descending with **stable** tie-breaking before calling `ax.bar`.

- [ ] 1.4 Keep the tool return format unchanged: markdown with embedded **PNG** data URI; no new dependencies.

## 2. Tests and quality gates

- [ ] 2.1 Extend `tests/test_chart_tools.py`: add or adjust tests so each **new** spec scenario in the delta has a matching pytest (e.g. bar sort order can be asserted by decoding PNG and sampling bar positions, or by testing a small package-private helper if extracted for sort logic; DPI/stylesheet can be covered via mocking `fig.savefig` kwargs or `matplotlib.rcParams` inside the render path—choose the most reliable approach).

- [ ] 2.2 Run `poetry run ruff check .` and `poetry run ruff format .`; fix any issues.

- [ ] 2.3 Run `poetry run bandit -c pyproject.toml -r src/`.

- [ ] 2.4 Run `poetry run pytest`.

- [ ] 2.5 Run `poetry run pip-audit`; address or document any findings.

## 3. OpenSpec and docs

- [ ] 3.1 After implementation, merge this change’s delta into `openspec/specs/chart-generation/spec.md` (ADDED requirements and scenarios) so main specs stay canonical.

- [ ] 3.2 No `docs/CONFIGURATION.md` or `config/settings.yaml` updates for this change unless optional `FINOPS_*` chart overrides are added (they are **not** in scope for the current proposal).
