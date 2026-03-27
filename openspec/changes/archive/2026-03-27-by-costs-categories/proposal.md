# By Cost Categories Dashboard — Proposal

## Why

FinOps users define **AWS Cost Categories** (account- or tag-based rules) to slice spend beyond service/account. The reference analysis in **`cost-categories-analysis-2026-03-27.md`** shows the value: list categories via **GetCostCategories**, then **GetCostAndUsage** grouped by `COST_CATEGORY` to see spend per dimension value, plus **coverage** (how much spend is categorized vs uncategorized/untagged). Today the hosted **costs dashboard** shows MTD by service, linked account, marketplace, recommendations, anomalies, and Savings Plans—but **not** cost categories, so users cannot see this view without external tools or the chat agent.

## What Changes

- **Backend:** Add Cost Explorer–backed logic to (1) discover cost category **names** available to the payer/management account, (2) for the **same MTD window** as the rest of the dashboard, fetch **UnblendedCost** grouped by each category’s dimension values, and (3) derive **coverage** metrics per category (e.g. categorized vs uncategorized spend and coverage %), aligned with the methodology in the markdown doc (totals as denominator; treat common “untagged”/empty bucket as uncategorized where applicable).
- **API:** Expose data via a **lazy dashboard slice** (same pattern as `/costs/dashboard/by-service`), e.g. **`GET /costs/dashboard/cost-categories`**, returning JSON the UI can render without loading heavy work on the initial dashboard bundle.
- **Web UI:** Add a **Costs dashboard** panel (section) that displays cost categories: optional **summary table** (category name, coverage %, categorized vs uncategorized spend) and **per-category** breakdown table (value, cost, % of total) with loading/error states consistent with other panels.
- **Demo mode:** If demo mode masks other cost data, apply the same masking rules to category **values** and amounts where identifiers could leak (follow existing demo patterns).
- **Docs:** Update **`docs/CONFIGURATION.md`** only if new **`FINOPS_`** or settings keys are introduced (prefer none for v1).

## Capabilities

### New Capabilities

- **`cost-categories-dashboard`**: Defines backend aggregation (GetCostCategories + GetCostAndUsage with `COST_CATEGORY` group), HTTP response shape for the lazy slice, demo-mode behavior, and the hosted UI panel (tables, MTD alignment, error handling).

### Modified Capabilities

- None at spec-file level if all behavior is captured under **`cost-categories-dashboard`**. If the team prefers normative text under **`backend-api`** / **`hosted-web-ui`**, a follow-up delta can merge; this proposal scopes a single cohesive capability first.

## Impact

- **`src/finops_buddy/costs.py`** (or a focused helper module): new functions calling `ce:get_cost_categories` / `get_cost_and_usage` with `GroupDefinitions` / `GroupBy` for `COST_CATEGORY`.
- **`src/finops_buddy/api/app.py`**: new route `/costs/dashboard/cost-categories` (or equivalent), profile and demo middleware consistent with existing dashboard slices.
- **`frontend/src/api/client.js`**: cached fetch helper mirroring other dashboard slices.
- **`frontend/src/components/DashboardSection.jsx`** (and possibly small presentational components): new panel and tables.
- **`tests/`**: pytest for aggregation helpers and API response shape; frontend tests if the project pattern supports them.
- **Dependencies:** No new Python packages expected (boto3 Cost Explorer already in use).
