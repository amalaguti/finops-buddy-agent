## Context

The **hosted costs dashboard** loads core MTD data and **lazy slices** (`/costs/dashboard/by-service`, `by-account`, etc.) via `frontend/src/api/client.js` and renders panels in **`DashboardSection.jsx`**. Cost data uses **`src/finops_buddy/costs.py`** (Cost Explorer `get_cost_and_usage`) with the same **month-to-date** window as existing dashboard endpoints.

**AWS Cost Categories** are management-account constructs. The analysis document (`cost-categories-analysis-2026-03-27.md`) uses:

1. **List category names** — Cost Explorer **`GetCostCategories`** (boto3: `get_cost_categories`).
2. **Spend grouped by category** — **`GetCostAndUsage`** with **`GroupBy`** / group definitions using **`Type: COST_CATEGORY`** and **`Key: <category_name>`** (per [Cost Explorer API](https://docs.aws.amazon.com/aws-cost-management/latest/APIReference/API_CostExplorer.html)).
3. **Coverage** — Compare total MTD to spend attributed to “untagged” / default bucket when present; otherwise coverage = 100% if all rows are explicit values.

IAM typically requires **`ce:GetCostCategories`** and **`ce:GetCostAndUsage`** on the payer (or delegated admin) scope; failures MUST surface as **403** with a clear message, consistent with other cost endpoints.

## Goals / Non-Goals

**Goals:**

- One **lazy API** endpoint returning structured JSON for **all** cost categories (names + per-category breakdown + coverage summary) for the **same MTD period** as the dashboard.
- **React panel** on the costs dashboard: summary table + expandable or tabbed per-category value tables (cost + % of total), aligned with the markdown report.
- **Demo mode**: mask identifiers in category **value** labels where they resemble account IDs or sensitive strings, using the same approach as other dashboard demo transforms.
- **Tests**: pytest for pure functions and API contract; Ruff/Bandit/pip-audit per project rules on apply.

**Non-Goals:**

- Editing or creating cost category rules in AWS (read-only).
- Historical period picker for this panel in v1 (reuse MTD only).
- CSV export of the panel (can be a follow-up).
- **Cost Explorer MCP** exposure; this is first-party API in `costs.py` / app.

## Decisions

### D1 — Single lazy endpoint vs embedding in `GET /costs/dashboard`

**Decision:** Add **`GET /costs/dashboard/cost-categories`** (same auth/profile/demo as other slices) and **do not** load it in the initial `GET /costs/dashboard` payload.

**Rationale:** Discovering categories plus N `get_cost_and_usage` calls can add latency; lazy load matches **`by-service`** / **`by-account`** pattern and keeps first paint fast.

**Alternative considered:** Single mega-response — rejected for latency and cache granularity.

### D2 — Server-side aggregation shape

**Decision:** Response JSON includes:

- **`period`**: `{ start, end }` (ISO dates) matching existing MTD helpers.
- **`categories`**: array of objects, each with:
  - **`name`**: cost category name (string).
  - **`total_cost`**: float (MTD unblended total for that grouping, should match sum of rows or overall total).
  - **`rows`**: `{ value_key, cost, pct_of_total }[]` where `value_key` is the CE dimension value (e.g. `prd`, `untagged`, `NoCostCategory` normalized for display).
  - **`coverage`**: `{ categorized_cost, uncategorized_cost, coverage_pct }` where uncategorized is derived from designated rows (e.g. keys matching `untagged`, empty, or `NoCostCategory` — **normalize in code** with a small allow-list of known “uncategorized” labels).

**Rationale:** Matches the report tables; frontend stays thin.

**Alternative:** Return raw CE response — rejected; harder to test and demo-mask.

### D3 — Boto3 API usage

**Decision:** Use `client.get_cost_categories` with the same **time period** as MTD `get_cost_and_usage`. Filter returned category **names** to those applicable to the request (document that empty list means no categories or insufficient permissions). For each name, call **`get_cost_and_usage`** with **`GroupBy=[{'Type':'COST_CATEGORY','Key': name}]`** and **`Metrics=['UnblendedCost']`**, **`Granularity`='MONTHLY`** (or **`DAILY`** rolled up server-side — prefer **MONTHLY** for MTD to match the doc).

**Rationale:** Aligns with the methodology document.

### D4 — Error handling

**Decision:** If **`get_cost_categories`** fails with access denied, return **403** with message; if **empty** categories, return **200** with `categories: []` and an optional **`info`** string for the UI.

### D5 — Frontend layout

**Decision:** New subsection under “Costs dashboard” with heading **“Cost categories”**, fetch on mount like other lazy panels (or when section expands if we add collapse — default **load on dashboard view** for parity with other panels).

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| **Many categories** → many CE calls → slow / throttling | **Sequential** calls with short timeouts; optional cap (e.g. first 20 categories) with `truncated: true` in JSON — document in **Open Questions** if product wants hard cap. |
| **Uncategorized row naming** varies by account | **Configurable normalization** list in code + tests for common labels. |
| **Non-payer** role may not see categories | Clear error; empty state copy in UI. |

## Migration Plan

- Deploy backend + frontend together; **no** DB migration.
- **Rollback:** Revert commit; remove route and panel.

## Open Questions

- Should we **cap** the number of categories per request (performance)?
- **Granularity:** Confirm **MONTHLY** bucket for partial month matches Finance expectations vs **DAILY** sum (spec can require **MONTHLY** for MTD to match the analysis doc).
