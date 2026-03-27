# savings-plans-recommendations — Tasks

**Branch:** Implement on a feature branch (e.g. `feature/savings-plans-recommendations`), not on `main`.

## 1. Backend — Cost Explorer

- [x] 1.1 Add helpers in `src/finops_buddy/costs.py` to iterate the full **`SavingsPlansType` × `TermInYears` × `PaymentOption`** matrix, call **`get_savings_plans_purchase_recommendation`** per cell with **`LookbackPeriodInDays`** `THIRTY_DAYS` (or equivalent), **no region `Filter`**, merge successful rows with matrix dimensions attached, and handle per-cell errors without dropping the whole payload when some cells succeed.
- [x] 1.2 Add **`GET /costs/dashboard/savings-plans-purchase-recommendations`** (or the path chosen in implementation) in `src/finops_buddy/api/app.py` with profile/demo handling consistent with other dashboard slices; return documented JSON (`lookback` / `period`, `recommendations`, optional `errors` if partial).
- [x] 1.3 Apply **demo-mode** masking to the response when `X-Demo-Mode: true`, reusing **`mask_response_data`** and extending keyed fields in `demo.py` only if new identifier-like strings appear in the payload.

## 2. Frontend

- [x] 2.1 Add a cached fetch in `frontend/src/api/client.js` (same session cache pattern as other dashboard slices) for the new endpoint.
- [x] 2.2 Add a **collapsible** **Savings Plans purchase recommendations** panel in `frontend/src/components/DashboardSection.jsx` **below** the **By cost categories** block: loading, empty, error, and a table of key columns; wire `markCostsLoaded` (or equivalent) if this fetch is part of the initial parallel batch.
- [x] 2.3 Run **`cd frontend && npm run build:hosted`** so `src/finops_buddy/webui/` is updated for packaged `finops serve`.

## 3. Tests and quality

- [x] 3.1 Add or extend **`tests/`** with pytest covering matrix helper behavior (mocked CE), partial failure behavior, and the new endpoint (success, access denied); map tests to spec **#### Scenario** names where practical.
- [x] 3.2 Run **`poetry run ruff check .`** and **`poetry run ruff format .`**; fix issues in touched code.
- [x] 3.3 Run **`poetry run bandit -c pyproject.toml -r src/`**; fix medium+ findings.
- [x] 3.4 Run **`poetry run pytest`** until green.
- [x] 3.5 Run **`poetry run pip-audit`** (pygments **CVE-2026-4539** ignored per **`docs/DEVELOPMENT.md`** until a fixed PyPI release exists).

## 4. Documentation

- [x] 4.1 Update **`docs/FEATURES.md`** with a short description of the purchase recommendations panel and the new endpoint (no new **`FINOPS_`** vars unless implemented).

## 5. OpenSpec sync (on apply)

- [x] 5.1 After implementation, merge **`openspec/changes/savings-plans-recommendations/specs/savings-plans-purchase-recommendations/spec.md`** into **`openspec/specs/savings-plans-purchase-recommendations/spec.md`**.
