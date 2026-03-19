# Tasks: Dashboard backend and UI expansion

## 1. Branch and setup

- [x] 1.1 Ensure you are not on `main`. Create or switch to a feature branch (e.g. `feature/dashboard-backend-ui-expansion`) before implementing.

## 2. Backend: Cost Explorer and cost functions

- [x] 2.1 In `src/finops_buddy/costs.py`, add a shared internal helper that calls Cost Explorer GetCostAndUsage with configurable optional Filter and GroupBy dimension (reuse time range and pagination pattern from existing code). Use it to implement `get_costs_by_service_aws_only(session, start=None, end=None)` with Filter BILLING_ENTITY = "AWS" and GroupBy SERVICE; return list of (service, cost) sorted descending.
- [x] 2.2 Implement `get_costs_by_linked_account(session, start=None, end=None)` and `get_costs_marketplace(session, start=None, end=None)` using the same helper (GroupBy LINKED_ACCOUNT; Filter BILLING_ENTITY = "AWS Marketplace" and GroupBy SERVICE respectively). Handle empty results; raise CostExplorerError on API errors.

## 3. Backend: Cost Optimization Hub, anomalies, and Savings Plans

- [x] 3.1 Add a module or functions (e.g. in `src/finops_buddy/optimization.py` or under `costs.py`) that call AWS Cost Optimization Hub ListRecommendations, sort/filter by estimated savings, and return the top 10 recommendations. On access denied or API error, return an empty list without raising.
- [x] 3.2 Add a function that calls Cost Explorer get_anomalies for the last 3 days (date interval). Return a list of anomaly entries (e.g. id, date range, impact). On access denied or no data, return an empty list without raising.
- [x] 3.3 Add a function that calls Cost Explorer get_savings_plans_utilization and get_savings_plans_coverage for a given period (1, 2, or 3 months). Return utilization and coverage metrics. On no Savings Plans or API error, return a safe default (e.g. zero or empty structure) without raising.

## 4. API: Dashboard endpoint

- [x] 4.1 In `src/finops_buddy/api/app.py`, add `GET /costs/dashboard` that resolves profile/session, calls the three cost functions plus optimization, anomalies, and savings plans functions, and builds the response with by_service_aws_only, by_account, by_marketplace, optimization_recommendations (top 10), anomalies (last 3 days), and savings_plans (utilization/coverage). Accept optional query param savings_plans_months (1, 2, or 3; default 1). Apply demo-mode masking to by_account and to account IDs in recommendations/anomalies. Return 400 when no profile, 403 on CostExplorerError for core cost data; on optional API failures (Cost Optimization Hub, GetAnomalies, Savings Plans), still return 200 with empty or default values for those sections. Document the route.

## 5. Frontend: Dashboard data and UI

- [x] 5.1 In `frontend/src/api/client.js`, add `getCostsDashboard(profile, options?)` that calls the dashboard endpoint (passing savings_plans_months when provided) and caches by profile + date + options (same strategy as existing getCosts).
- [x] 5.2 Add dashboard UI components: a block that fetches via `getCostsDashboard(profile, { savings_plans_months })` and displays six sections—costs by AWS service, by account, by marketplace; optimization recommendations (top 10); anomalies (last 3 days); Savings Plans utilization/coverage. Use compact tables or cards; show loading and error states; show explicit empty-state messages for each section when data is empty.
- [x] 5.3 Add a Savings Plans period picker (dropdown or tabs) for 1, 2, or 3 months; when the user changes the selection, refetch dashboard with the new savings_plans_months and update the Savings Plans section.
- [x] 5.4 Update `frontend/src/layouts/LayoutSidebar.jsx` to render the dashboard block (all six sections) in the sidebar, replacing or supplementing the single CostsSection so the layout remains Account + dashboard sections + main content; use collapsible sections or tabs if needed for space.

## 6. Agent tools (optional)

- [x] 6.1 In `src/finops_buddy/agent/tools.py`, change the current-period cost tool to use `get_costs_by_service_aws_only` instead of `get_costs_by_service` so chat and dashboard both show AWS-only for "current month by service."

## 7. Documentation

- [x] 7.1 Update README.md (or docs) to describe the full dashboard: the six sections (costs by AWS service, by account, by marketplace; cost optimization recommendations top 10; cost anomalies last 3 days; Savings Plans utilization/coverage with 1/2/3 month picker), that the dashboard is loaded from `GET /costs/dashboard` with optional savings_plans_months; mention demo-mode masking and required IAM permissions for Cost Optimization Hub, GetAnomalies, and Savings Plans where applicable.

## 8. Quality and verification

- [x] 8.1 Run `poetry run ruff check .` and `poetry run ruff format .`; fix any issues.
- [x] 8.2 Run `poetry run bandit -c pyproject.toml -r src/`; fix any medium or high severity findings (or document/suppress with justification).
- [x] 8.3 Add or extend pytest unit tests: cover the new cost functions and optimization/anomalies/savings-plans functions (mocked AWS APIs) and the dashboard endpoint (profile, demo masking, savings_plans_months, partial failure behavior) in `tests/test_costs.py`, `tests/test_api.py`, and any new test file for optimization/anomalies; add frontend tests for the dashboard (loading, error, empty states, period picker) where practical.
- [x] 8.4 Run `poetry run pip-audit`; address or document any reported vulnerabilities.
