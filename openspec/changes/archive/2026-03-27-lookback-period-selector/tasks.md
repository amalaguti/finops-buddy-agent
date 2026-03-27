# lookback-period-selector — Tasks

**Branch:** Implement on a feature branch (e.g. `feature/lookback-period-selector`), not on `main`.

## 1. Backend — period presets and API

- [x] 1.1 In `src/finops_buddy/costs.py`, add a small helper (e.g. `dashboard_period_to_date_range`) mapping **`mtd`**, **`7d`**, **`30d`**, **`60d`**, **`90d`** to `(start, end)` ISO strings; **`mtd`** SHALL delegate to **`_current_month_range()`**; rolling presets SHALL use **N** calendar days **including today** (`start = today - (N - 1)`, `end = today + 1`). Raise **`ValueError`** for invalid tokens.
- [x] 1.2 In `src/finops_buddy/api/app.py`, add optional query **`period`** (default **`mtd`**) to **`GET /costs/dashboard/by-service`** and **`GET /costs/dashboard/by-account`**, resolve dates, pass **`start`/`end`** into **`get_costs_by_service_aws_only`** and **`get_costs_by_linked_account`**; on **`ValueError`** return **400** with a clear **`detail`**.
- [x] 1.3 Add pytest tests (e.g. in `tests/test_costs.py` and `tests/test_api.py`) mapping to spec scenarios: default/Omitted behaves as MTD; **`30d`** uses rolling window; invalid **`period`** returns **400**; name tests after **`#### Scenario`** titles where practical.

## 2. Frontend — selector and cache

- [x] 2.1 In `frontend/src/api/client.js`, extend **`dashboardSliceCacheKey`** (or equivalent) so by-service and by-account cache keys include the **period preset**; append **`period=...`** to requests for those two endpoints.
- [x] 2.2 In `frontend/src/components/DashboardSection.jsx`, add a **single** lookback control (select or button group) with options **Month to date**, **Last 7 / 30 / 60 / 90 days**; default **Month to date**; wire **`getCostsDashboardByService`** and **`getCostsDashboardByAccount`** to use the same state; update the two **`MiniTable`** titles/section copy so they do not always say “month to date” when another period is active.
- [x] 2.3 Run **`cd frontend && npm run build:hosted`**.

## 3. Documentation

- [x] 3.1 Update **`docs/FEATURES.md`** with the dashboard lookback selector and that drill-down rows may still be MTD unless documented otherwise.
- [x] 3.2 Update **`docs/CONFIGURATION.md`** with the **`period`** query parameter for **`/costs/dashboard/by-service`** and **`/costs/dashboard/by-account`** (allowed values, default).
- [x] 3.3 If new users need a direct link, add a **one-line pointer** in root **`README.md`** to the configuration section (only if not already discoverable).

## 4. Verification

- [x] 4.1 Run **`poetry run ruff check .`** and **`poetry run ruff format .`**; fix issues.
- [x] 4.2 Run **`poetry run bandit -c pyproject.toml -r src/`**; fix medium+ findings.
- [x] 4.3 Run **`poetry run pytest`** until green.
- [x] 4.4 Run **`poetry run pip-audit`**; address or document per **`docs/DEVELOPMENT.md`**.

## 5. OpenSpec sync (on apply)

- [x] 5.1 After implementation, add **`openspec/specs/costs-dashboard-lookback/spec.md`** from the delta under **`openspec/changes/lookback-period-selector/specs/costs-dashboard-lookback/spec.md`** (canonical spec for the new capability).
