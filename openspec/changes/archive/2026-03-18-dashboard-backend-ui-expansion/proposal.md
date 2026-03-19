# Proposal: Dashboard backend and UI expansion

## Why

The FinOps Buddy UI today shows a single "Current month costs" table (by service) in the sidebar, which mixes AWS services with AWS Marketplace and does not show costs by linked account. Users need at-a-glance visibility into current-month costs split by AWS services only, by linked account, and by marketplace products, in a dashboard-style layout.

## What Changes

- **Backend:** Add three current-month cost retrieval paths using Cost Explorer with appropriate filters and dimensions: (1) by service with BILLING_ENTITY = "AWS" only (exclude Marketplace), (2) by linked account, (3) marketplace only (BILLING_ENTITY = "AWS Marketplace", grouped by product/service). Add retrieval for: (4) cost optimization recommendations from Cost Optimization Hub (top 10 by savings opportunity), (5) cost anomalies detected in the last 3 days (Cost Anomaly Detection / GetAnomalies), (6) Savings Plans utilization and coverage for a selectable period (1, 2, or 3 months). Add a single API endpoint that returns all dashboard data (cost breakdowns plus recommendations, anomalies, savings plans).
- **API:** New endpoint `GET /costs/dashboard` returning `by_service_aws_only`, `by_account`, `by_marketplace`, `optimization_recommendations` (top 10), `anomalies` (last 3 days), and `savings_plans` (utilization and coverage for a chosen period). Support an optional query parameter (e.g. `savings_plans_months=1|2|3`) for the Savings Plans lookback; reuse existing profile and demo-mode behavior; mask account IDs where applicable.
- **Frontend:** Redesign the layout to a dashboard style: a dedicated dashboard block showing six sections—(1) current month by AWS service, (2) by linked account, (3) marketplace only, (4) cost optimization recommendations (top 10 by savings), (5) cost anomalies (last 3 days), (6) Savings Plans utilization and coverage with a period picker (1, 2, or 3 months). Add `getCostsDashboard(profile, options?)` and components to render all sections with loading and empty states.
- **Agent (optional):** Align in-process "current period by service" with AWS-only so chat and UI are consistent; optionally add tools for by-account and marketplace for chat.
- **Docs and tests:** Document the new dashboard, endpoint, and new AWS API usage (Cost Optimization Hub, GetAnomalies, Savings Plans); add unit tests for the new functions and API, and frontend tests for the dashboard.

No breaking changes: existing `GET /costs` remains for backward compatibility.

## Capabilities

### New Capabilities

- `costs-dashboard`: Backend and API for the full dashboard: current-month cost breakdowns (by AWS service only, by linked account, by marketplace); cost optimization recommendations from Cost Optimization Hub (top 10 by savings); cost anomalies in the last 3 days (GetAnomalies); Savings Plans utilization and coverage for 1/2/3 months (selectable). Covers Cost Explorer, Cost Optimization Hub, and Cost Anomaly Detection APIs; the `GET /costs/dashboard` endpoint with optional `savings_plans_months` and demo masking.

### Modified Capabilities

- `backend-api`: Add requirement for HTTP endpoint that returns the full costs dashboard: cost breakdowns (by_service_aws_only, by_account, by_marketplace), optimization_recommendations (top 10), anomalies (last 3 days), and savings_plans (utilization/coverage for 1/2/3 months via query param), for a given or default profile.
- `hosted-web-ui`: Add requirement for dashboard-style layout with six sections: three current-month cost sections, cost optimization recommendations (top 10), cost anomalies (last 3 days), and Savings Plans utilization/coverage with a period picker (1/2/3 months), using the dashboard API and appropriate empty/error states.

## Impact

- **Code:** `src/finops_buddy/costs.py` (cost functions), new or extended module for Cost Optimization Hub and Cost Anomaly Detection (e.g. `src/finops_buddy/optimization.py` or under `costs.py`), `src/finops_buddy/api/app.py` (dashboard route), `frontend/src/api/client.js`, `frontend/src/components/`, `frontend/src/layouts/LayoutSidebar.jsx`. Optionally `src/finops_buddy/agent/tools.py`.
- **APIs:** New `GET /costs/dashboard` (with optional `savings_plans_months`); existing `GET /costs` unchanged. Backend calls AWS Cost Explorer, Cost Optimization Hub (ListRecommendations), GetAnomalies (CE), get_savings_plans_utilization / get_savings_plans_coverage (CE).
- **Dependencies:** boto3 (already present); Cost Optimization Hub and Cost Anomaly Detection require additional IAM permissions (e.g. `cost-optimization-hub:ListRecommendations`, `ce:GetAnomalies`, CE Savings Plans APIs).
- **Config:** No new env vars; reuse existing profile and demo mode.
