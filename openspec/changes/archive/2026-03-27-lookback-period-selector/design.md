## Context

The hosted dashboard loads **`/costs/dashboard/by-service`** and **`/costs/dashboard/by-account`** via `getCostsDashboardByService` / `getCostsDashboardByAccount` in `client.js`, with cache keys `profile:todayKey:slice`. Backend endpoints call `get_costs_by_service_aws_only` and `get_costs_by_linked_account`, which already accept optional **`start` / `end`** (ISO `YYYY-MM-DD`, **end exclusive** per Cost Explorer).

## Goals / Non-Goals

**Goals:**

- One **period preset** query parameter on **both** endpoints (same allowed values, same semantics).
- **Default** when the parameter is omitted: **month-to-date** — identical to today’s behavior (backward compatible for callers that do not send the parameter).
- **Rolling windows:** “Last *N* days” means a rolling window of **N** calendar days **including today**: `start = today - (N - 1)`, `end = today + 1` (exclusive), using the same **local `date.today()`** convention as `_current_month_range()`.
- **Frontend:** One React state value (e.g. `dashboardPeriodPreset`) drives both fetches; labels for the two tables reflect the selection.
- **Cache:** Include the preset in the client cache key (along with profile and existing date key if still used) so switching away and back does not refetch.

**Non-Goals:**

- Changing Marketplace, recommendations, anomalies, Savings Plans, or cost-categories slices in this change.
- Changing **drill-down** endpoints (`/costs/by-service-accounts`, `/costs/by-account-services`) — they remain **MTD** until a follow-up; document the mismatch if the top tables use a rolling window.
- Persisting the selected period across browser sessions.

## Decisions

1. **Query parameter** name **`period`**, allowed values: **`mtd`**, **`7d`**, **`30d`**, **`60d`**, **`90d`**. Invalid or unknown values → **400** with a clear message.

2. **Backend helper** in `costs.py`, e.g. `dashboard_period_to_date_range(period: str) -> tuple[str, str]`, delegating to `_current_month_range()` for `mtd` and a small `_rolling_days_range(days: int)` for `7`, `30`, `60`, `90`.

3. **Response shape:** Keep **JSON array** body for both endpoints (no wrapper) to avoid breaking clients that expect a raw list; period is implied by the request and reflected in the UI.

4. **Frontend cache key:** Extend `dashboardSliceCacheKey` (or parallel) to `profileKey + periodPreset + dateKey` where `dateKey` remains `todayKey()` so cache invalidates at day boundary when appropriate.

## Risks / Trade-offs

- **[Risk]** Drill-down MTD vs top table rolling window confuses users → **Mitigation:** short note in `docs/FEATURES.md`; optional follow-up to thread period into drill-down APIs.
- **[Risk]** Large `N` + heavy accounts → **Mitigation:** same CE limits as today; no extra calls beyond user selection.

## Migration Plan

Deploy backend and frontend together; old clients omit `period` and keep MTD.

## Open Questions

None.
