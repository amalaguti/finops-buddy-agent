## Context

The hosted dashboard already loads **Savings Plans utilization/coverage** and **cost optimization recommendations** (different APIs). AWS **purchase** recommendations come from **`GetSavingsPlansPurchaseRecommendation`**, which requires **one** `SavingsPlansType`, **one** `TermInYears`, and **one** `PaymentOption` per call. There is no single “all recommendations” call. The methodology document (`savings-plans-recommendations-2026-03-27.md`) lists the 3×2×3 parameter matrix (18 calls) and key response fields (hourly commitment, estimated savings, utilization, ROI, etc.).

## Goals / Non-Goals

**Goals:**

- For the **management/payer** profile session, call **`get_savings_plans_purchase_recommendation`** (boto3) for **every** supported combination of:
  - **SavingsPlansType:** `COMPUTE_SP`, `EC2_INSTANCE_SP`, `SAGEMAKER_SP` (verify against current botocore model if AWS adds types).
  - **TermInYears:** `ONE_YEAR`, `THREE_YEARS`.
  - **PaymentOption:** `NO_UPFRONT`, `PARTIAL_UPFRONT`, `ALL_UPFRONT`.
- Use a **single lookback**, default **`THIRTY_DAYS`** (aligned with the analysis doc), unless we need configurability later.
- **Do not** apply a **region** `Filter` (or any filter that would hide global recommendations). Omit `Filter` unless the API requires it for the account—goal is “see all” recommendations AWS returns for each matrix cell.
- Normalize successful responses into a **list of rows** tagged with the query tuple (`savings_plans_type`, `term_in_years`, `payment_option`) plus flattened metrics from `SavingsPlansPurchaseRecommendation` / details as returned by AWS (see doc table: `HourlyCommitmentToPurchase`, `EstimatedSavingsAmount`, `EstimatedMonthlySavingsAmount`, `EstimatedAverageUtilization`, `EstimatedROI`, etc.—map what the API actually returns).
- On **empty** or **no recommendation** for a cell, skip or include an explicit empty entry—prefer **only rows with actionable data** to keep the UI small.
- Expose **`GET /costs/dashboard/savings-plans-purchase-recommendations`** (or a name consistent with existing routes) with the same **profile resolution** and **demo masking** as other lazy slices.
- **Frontend:** collapsible section **below** the “By cost categories” block in `DashboardSection.jsx`, same UX pattern (expand/collapse, loading/error/empty), session-scoped cache like other slices.
- **`npm run build:hosted`** after UI changes.

**Non-Goals:**

- Purchasing Savings Plans or write operations.
- Persisting recommendations in a database.
- Running fewer than the full matrix by default (user asked for all types); optional future env to limit combinations is out of scope unless needed for throttling.

## Decisions

### D1 — Full 18-query matrix per lazy load

**Decision:** Run all 18 parameter combinations sequentially (or limited concurrency with a small cap to avoid throttling), merge results.

**Rationale:** User requested all plan types and no arbitrary subset; matches analysis doc.

**Alternative:** Sample 3 queries only—rejected.

### D2 — Error handling per cell

**Decision:** If one cell returns `AccessDenied` or `ValidationException`, record an error for that cell (or fail the whole endpoint with a clear message—prefer **partial results** with per-cell errors only if API noise is high; otherwise **fail fast** on first `AccessDenied` for consistency with other CE endpoints). **Recommendation:** collect per-call errors into an optional `errors[]` or log and skip failed cells so the panel still shows partial data.

**Rationale:** Throttling or missing permission for one combination should not blank the entire panel if others succeed.

### D3 — Response JSON shape

**Decision:** Return `{ period: { lookback_period_in_days }, recommendations: [...], optional truncated/errors }` where each item includes identifiers for the matrix dimensions plus numeric/string fields needed for the table.

**Rationale:** Stable contract for React tables and tests.

### D4 — Demo mode

**Decision:** Run existing `mask_response_data` on the payload; extend demo key list if new string fields (e.g. account hints) appear in nested objects.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| **18 CE calls** slow or throttled | Sequential calls with short backoff on `Throttling`; document expected latency; optional small concurrency (e.g. 3–5) if safe. |
| **Large payloads** | Return only fields needed for the table; cap row list if AWS returns huge detail arrays (unlikely for purchase recommendation summary). |
| **Permission gaps** | Clear 403 message if `GetSavingsPlansPurchaseRecommendation` denied. |

## Migration Plan

- Deploy backend + frontend together.
- **Rollback:** revert commit; remove route and panel.

## Open Questions

- Whether **`AccountScope`** should be set (e.g. `PAYER` vs linked)—default to AWS/boto3 default for payer context; document in implementation.
- Exact **output field names** from boto3 response—implementer SHALL map from live `GetSavingsPlansPurchaseRecommendation` response structure and unit-test with fixtures.
