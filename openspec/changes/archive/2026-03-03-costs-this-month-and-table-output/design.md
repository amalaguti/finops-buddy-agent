# Design: Costs This Month and Table Output

## Context

Change 1 provides session resolution and identity. This change adds cost retrieval and table formatting so users can run e.g. `finops costs` and see current-month costs by service. We use the AWS Cost Explorer API (GetCostAndUsage) with GROUP_BY SERVICE and a month-to-date time range. Output is terminal-friendly (no HTML/JS).

## Goals / Non-Goals

**Goals:**
- Call Cost Explorer GetCostAndUsage for the current calendar month (start of month to today).
- Group by SERVICE dimension; use UnblendedCost (or configurable metric).
- Render results as a readable table (service name, cost, optional %).
- Reuse session from Change 1 (profile/env); no new credential mechanism.

**Non-Goals:**
- Cost anomalies, Savings Plans, RI, or other cost features (later changes).
- Caching or persistence of cost data.
- Backend API or frontend.

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **API** | boto3 client `ce.get_cost_and_usage` | Standard way to get cost by service; filter by time range and group by SERVICE. |
| **Metric** | UnblendedCost | Common for “what I’m charged”; matches Billing and Cost Management MCP guidance. |
| **Date range** | Current calendar month (start to today or yesterday) | “Costs this month” per PROJECT_CONTEXT; avoid partial today if API lags (use yesterday as end if needed). |
| **Table formatting** | Stdlib-only (string formatting, column widths) or minimal dependency (e.g. tabulate) | Keep CLI dependency set small; tabulate is optional if we want aligned columns with little code. |
| **CLI** | Subcommand `costs` with optional `--profile`, optional `--no-header` | Consistent with existing `whoami` / `profiles` / `context`. |

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Cost Explorer not enabled | Document that Cost Explorer must be enabled in the account; fail with a clear message if access denied or no data. |
| API costs | Cost Explorer API has a cost per request; document and keep requests minimal (one request for month-to-date). |
| Large number of services | Limit or paginate (e.g. top N by cost) to keep table readable; default e.g. top 20 or all. |

## Migration Plan

- Add cost module and table formatter; add `costs` subcommand. No breaking changes to existing commands. No rollback beyond code revert.

## Open Questions

- Whether to show “top N” services by default (e.g. 20) or all; can be decided in tasks (e.g. `--top 20` flag).
