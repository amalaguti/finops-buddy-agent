# Design: Dashboard backend and UI expansion

## Context

The FinOps Buddy UI currently shows one "Current month costs" table in the sidebar (from `GET /costs`), which returns costs grouped by SERVICE with no filter—so "AWS Marketplace" appears as a service row and linked-account breakdown is unavailable. The backend has a single cost path: `get_costs_by_service` in `costs.py` calling Cost Explorer with `GroupBy: SERVICE`. The proposal adds three cost views (AWS-only by service, by linked account, marketplace only) and a dashboard-style UI that displays all three.

## Goals / Non-Goals

**Goals:**

- Expose current-month costs in three forms: by AWS service only (exclude Marketplace), by linked account, and marketplace-only, via a single dashboard API and reusable cost functions.
- Add cost optimization recommendations (Cost Optimization Hub, top 10 by savings opportunity), cost anomalies (last 3 days), and Savings Plans utilization/coverage (1/2/3 months selectable) to the dashboard API and UI.
- Redesign the UI so all six dashboard sections are visible (cost breakdowns, recommendations, anomalies, savings plans) with loading and empty states, and a period picker for Savings Plans.
- Preserve backward compatibility: keep `GET /costs` unchanged; new behavior is additive.
- Apply demo-mode masking to the dashboard response (e.g. account IDs in `by_account` and any account identifiers in recommendations/anomalies).

**Non-Goals:**

- Changing how `GET /costs` behaves (no switch to AWS-only there in this change).
- Resolving linked account ID to human-readable name in the API (optional later).
- New env vars or settings; reuse existing profile and demo mode.
- Full Cost Optimization Hub filtering (e.g. by action type); top 10 by savings is sufficient for dashboard.

## Decisions

### 1. Single dashboard endpoint vs multiple endpoints

**Decision:** One endpoint `GET /costs/dashboard` that returns all three breakdowns in one response.

**Rationale:** One round-trip for the frontend, one place to apply demo masking and profile resolution. Alternative (e.g. `GET /costs?groupBy=service|account|marketplace` or separate paths) would require three requests or a more complex client and duplicate masking logic.

### 2. Cost Explorer filter for AWS vs Marketplace

**Decision:** Use the **BILLING_ENTITY** dimension: `Filter: { "Dimensions": { "Key": "BILLING_ENTITY", "Values": ["AWS"] } }` for AWS-only, and `Values: ["AWS Marketplace"]` for marketplace-only.

**Rationale:** BILLING_ENTITY is the documented way to separate AWS services from AWS Marketplace in Cost Explorer. Filtering by SERVICE ≠ "AWS Marketplace" would miss edge cases; BILLING_ENTITY is explicit.

### 3. Shared Cost Explorer helper vs three separate functions

**Decision:** Implement three named functions (`get_costs_by_service_aws_only`, `get_costs_by_linked_account`, `get_costs_marketplace`) that call a shared internal helper (e.g. parametrized by optional Filter and GroupBy key) to avoid duplicating pagination and error handling.

**Rationale:** Keeps the public API clear for callers and tests while sharing the pagination/request logic. Alternative: one generic `get_costs_grouped(filter=..., group_by=...)`—rejected to keep function names self-documenting and avoid a wide generic API.

### 4. Dashboard layout placement

**Decision:** Place the dashboard block in the **sidebar** (Option B from the plan): left column = Account + the three cost sections (e.g. stacked or accordions: "By AWS service", "By account", "Marketplace"); right column = main content (chat). Option A (dashboard strip above chat) would push chat down and require more vertical space; the current layout already has a resizable sidebar, so adding the three sections there keeps "cost at a glance" without changing the main content area.

**Rationale:** Fits existing LayoutSidebar structure; users already look at the sidebar for costs. If the team later prefers a top strip, the same data and components can be reused.

### 5. Agent tools alignment

**Decision:** In this change, do **not** add new agent tools for by-account or marketplace; optionally switch the existing "current period by service" tool to use `get_costs_by_service_aws_only` so chat and dashboard both show AWS-only when discussing "current month by service." Document that MCP Billing/Cost Management can provide by-account and marketplace in chat if enabled.

**Rationale:** Keeps the change focused on backend + API + UI; agent tool expansion can be a follow-up. Switching to AWS-only for the existing tool avoids user confusion (dashboard says "AWS only," chat says "all services").

### 6. Cost Optimization Hub and anomalies

**Decision:** Use AWS Cost Optimization Hub `ListRecommendations` (boto3 client `cost-optimization-hub`) to fetch recommendations; sort or filter by estimated savings and return the top 10. Use Cost Explorer `get_anomalies` (boto3 CE client) with a date interval for the last 3 days to fetch cost anomalies. Both are optional: if the account lacks permissions or the service is not enabled, return empty lists and do not fail the whole dashboard (or surface a section-level error in the UI).

**Rationale:** ListRecommendations returns all recommendations with savings data; we limit to 10 for dashboard readability. GetAnomalies is the standard API for Cost Anomaly Detection. Degrading gracefully when permissions are missing keeps the dashboard usable for accounts that only have Cost Explorer.

### 7. Savings Plans period

**Decision:** Expose a query parameter `savings_plans_months` (e.g. 1, 2, or 3) on `GET /costs/dashboard`; default to 1. The backend computes the time range (e.g. last N full months or trailing N months from today) and calls `get_savings_plans_utilization` and `get_savings_plans_coverage` with that range. The frontend provides a picker (dropdown or tabs) so the user can select 1, 2, or 3 months; changing the selection triggers a refetch with the new parameter.

**Rationale:** Single endpoint stays simple; the picker gives users the requested flexibility without multiple endpoints.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Cost Explorer BILLING_ENTITY values differ by region or over time | Use documented values "AWS" and "AWS Marketplace"; if API returns different values, handle empty results and log; consider fallback to SERVICE filter only if needed. |
| Dashboard endpoint does multiple API calls per request | Acceptable for single-user; consider caching (e.g. TTL by profile + month) later. If Cost Optimization Hub or GetAnomalies fail (e.g. no permission), return empty lists for those sections so the rest of the dashboard still loads. |
| Sidebar becomes long with six sections | Use compact tables, collapsible/accordion sections, or tabs so the sidebar stays usable; prioritize cost breakdowns and savings plans at top if needed. |
| Demo masking for `by_account` inconsistent with existing masking | Reuse the same mask logic as for context/costs (e.g. account ID mapping); apply to recommendations and anomalies where account IDs appear; document that dashboard is masked when X-Demo-Mode is set. |
| Cost Optimization Hub or Anomaly Detection not enabled | Return empty lists for optimization_recommendations and anomalies when the respective API returns access denied or no data; document required IAM permissions in README. |

## Migration Plan

- No data or config migration. Deploy backend with new cost functions and `GET /costs/dashboard`; deploy frontend that calls the new endpoint and renders the three sections. Existing `GET /costs` and current CostsSection (if still used elsewhere) remain unchanged.
- Rollback: revert frontend to a single costs section using `GET /costs`; optionally leave the dashboard route returning 501 or remove it if no other clients use it.

## Open Questions

- None blocking. Optional follow-ups: agent tools for by-account/marketplace; resolving account ID to name in the dashboard; caching for the dashboard response.
