# by-costs-categories — Tasks

**Branch:** Implement on a feature branch (e.g. `feature/by-costs-categories`), not on `main`.

## 1. Backend — Cost Explorer

- [x] 1.1 Add helpers in `src/finops_buddy/costs.py` (or a small module) to call **`get_cost_categories`** for the dashboard MTD window and to call **`get_cost_and_usage`** grouped by **`COST_CATEGORY`** for each category name; normalize rows, totals, uncategorized detection, and coverage %.
- [x] 1.2 Add **`GET /costs/dashboard/cost-categories`** in `src/finops_buddy/api/app.py` with profile/demo handling consistent with other dashboard slices; return documented JSON (`period`, `categories` with `rows`, `coverage`, etc.).
- [x] 1.3 Apply **demo-mode** masking to category value strings when `X-Demo-Mode: true`, reusing existing dashboard masking utilities.

## 2. Frontend

- [x] 2.1 Add **`getCostsDashboardCostCategories`** (or equivalent) in `frontend/src/api/client.js` with the same session cache pattern as other dashboard slices.
- [x] 2.2 Add the **Cost categories** panel to `frontend/src/components/DashboardSection.jsx` (loading, empty, error, tables for summary + per-category breakdown).
- [x] 2.3 Run **`cd frontend && npm run build:hosted`** so `src/finops_buddy/webui/` is updated for packaged `finops serve`.

## 3. Tests and quality

- [x] 3.1 Add or extend **`tests/`** with pytest covering aggregation helpers and the new endpoint (success, empty categories, error paths); map tests to spec **#### Scenario** names where practical.
- [x] 3.2 Run **`poetry run ruff check .`** and **`poetry run ruff format .`**; fix issues in touched code.
- [x] 3.3 Run **`poetry run bandit -c pyproject.toml -r src/`**; fix medium+ findings.
- [x] 3.4 Run **`poetry run pytest`** until green.
- [x] 3.5 Run **`poetry run pip-audit`** (use **`--ignore-vuln`** only with documentation per project rules if needed).

## 4. Documentation

- [x] 4.1 Update **`docs/FEATURES.md`** or **`docs/CONFIGURATION.md`** with a short description of the cost categories dashboard panel and endpoint if end users need it (no new **`FINOPS_`** vars unless implemented).

## 5. OpenSpec sync (on apply)

- [x] 5.1 After implementation, merge **`openspec/changes/by-costs-categories/specs/cost-categories-dashboard/spec.md`** into **`openspec/specs/cost-categories-dashboard/spec.md`**.
