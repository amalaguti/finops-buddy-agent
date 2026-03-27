## Why

The costs dashboard **By AWS service** and **By linked account** tables always reflect **month-to-date** spend. Operators often need **rolling windows** (e.g. last 7 or 30 days) to compare with short-term patterns or external reports. A single, explicit control avoids duplicate filters and keeps both tables consistent.

## What Changes

- Add a **lookback period selector** on the costs dashboard (same control for both tables): **Month to date** (default), **Last 7 days**, **Last 30 days**, **Last 60 days**, **Last 90 days**.
- **Backend:** Extend **`GET /costs/dashboard/by-service`** and **`GET /costs/dashboard/by-account`** with a documented query parameter (e.g. `period`) mapping to those presets. Resolve each preset to Cost Explorer **`start` / `end`** (exclusive end) dates and pass them into existing **`get_costs_by_service_aws_only`** / **`get_costs_by_linked_account`** helpers (already accept optional `start` / `end`). Default parameter value preserves **current month-to-date** behavior (**not** a breaking change for clients that omit the parameter).
- **Frontend:** One piece of UI state drives both fetches; table titles/subcopy reflect the selected period (replacing hard-coded “month to date” where appropriate for those two tables).
- **Session cache:** Extend client-side dashboard slice cache keys to include the selected period so each preset is fetched at most once per session unless the user changes profile or period again (same pattern as existing `dashboardSliceCacheKey` + `Map` caches).

## Capabilities

### New Capabilities

- `costs-dashboard-lookback`: Costs dashboard **by-service** and **by-account** HTTP slices support a **period preset** query parameter; UI exposes a single selector; session-scoped fetch caching includes the period.

### Modified Capabilities

_(none — existing specs do not define these two lazy slices in detail.)_

## Impact

- **Backend:** `src/finops_buddy/costs.py` (date-range helpers for presets), `src/finops_buddy/api/app.py` (query params + pass-through to cost helpers).
- **Frontend:** `frontend/src/api/client.js`, `frontend/src/components/DashboardSection.jsx` (and any small label copy).
- **Docs:** `docs/FEATURES.md`, **`docs/CONFIGURATION.md`** (query parameter for the two endpoints).
- **Tests:** `tests/test_costs.py` / `tests/test_api.py` for preset parsing and API wiring; **`npm run build:hosted`** after UI changes.

**Non-goal (this change):** Other dashboard slices (Marketplace, recommendations, drill-down **by service for account** / **by account for service**) stay on their current date logic unless explicitly extended later; document if drill-down remains MTD while top tables use a rolling window.
