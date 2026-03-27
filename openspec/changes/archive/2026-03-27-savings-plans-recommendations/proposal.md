# Proposal: Savings Plans purchase recommendations (dashboard)

## Why

The hosted costs dashboard already shows **Savings Plans utilization/coverage** and **cost optimization recommendations**, but it does not surface **Savings Plans *purchase* recommendations** from Cost Explorer (`GetSavingsPlansPurchaseRecommendation`). Finance and FinOps users need a consolidated view of AWS-generated purchase options (Compute SP, EC2 Instance SP, SageMaker SP, terms, payment options) without leaving the app. The analysis in `savings-plans-recommendations-2026-03-27.md` documents the API contract and useful response fields.

## What Changes

- Add backend support to call **`GetSavingsPlansPurchaseRecommendation`** for a **full matrix** of mandatory parameter combinations: all supported **`savings-plans-type`** × **`term-in-years`** × **`payment-option`** values (18 combinations per the API), with a single **lookback** (e.g. 30 days) and **no region filter** unless the API requires it—aggregate and return **all** non-empty recommendations the payer account returns.
- Expose a **lazy HTTP slice** (same profile/demo pattern as other `/costs/dashboard/*` endpoints) returning normalized rows for the UI.
- Add a **collapsible panel** on the costs dashboard **below “By cost categories”**, with loading/empty/error states and a table (or tables) of recommendations including key metrics (e.g. hourly commitment, estimated savings, utilization, ROI) as available from the API.
- Apply **demo-mode masking** to sensitive strings in the payload (consistent with other dashboard slices).
- Tests (pytest), Ruff/Bandit, pip-audit per project rules on apply.

## Capabilities

### New Capabilities

- `savings-plans-purchase-recommendations`: Cost Explorer purchase-recommendation aggregation (full parameter matrix), lazy API contract, and hosted UI panel placement below by-cost-categories; demo masking and error handling consistent with dashboard slices.

### Modified Capabilities

- (none at spec level beyond new capability; implementation touches `DashboardSection.jsx` and API modules in-repo.)

## Impact

- **Code:** `src/finops_buddy/costs.py` (new helpers), `src/finops_buddy/api/app.py` (new route), `frontend/src/api/client.js` (cached fetch), `frontend/src/components/DashboardSection.jsx` (panel below cost categories).
- **AWS:** Requires Cost Explorer permissions for `GetSavingsPlansPurchaseRecommendation` (and typical `ce:GetCostAndUsage` parity where applicable); **up to 18 CE calls** per dashboard load for the slice—document latency/throttling risk in design.
- **Docs:** `docs/FEATURES.md` pointer; no new `FINOPS_` variables unless we add optional tuning (prefer defaults first).
