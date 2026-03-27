## Why

The **By cost categories** section is expanded by default so users see the **Summary by cost category rule** table immediately. Below that, each rule’s **detail** table (dimension values, costs, % of category total) is always visible, which makes the block long and noisy when many rules exist. Users should be able to drill into per-rule detail only when needed.

## What Changes

- Keep the outer **By cost categories** collapsible block **expanded by default** (unchanged).
- Keep **Summary by cost category rule** visible whenever the outer block is expanded (unchanged position: first content inside the section).
- Wrap each **per-rule detail** table (one per cost category name) in its own **expand/collapse** control, matching the pattern used elsewhere on the dashboard (e.g. chevron, `aria-expanded`).
- **Default state** for each per-rule detail panel: **collapsed** (summary remains the primary view until the user expands a rule).

## Capabilities

### New Capabilities

_(none — behavior extends the existing cost-categories dashboard UI.)_

### Modified Capabilities

- `cost-categories-dashboard`: Extend the costs dashboard UI requirement so per-rule detail tables are collapsible child panels, collapsed by default, while the summary table stays always visible under the expanded parent section.

## Impact

- **Frontend:** `frontend/src/components/DashboardSection.jsx` (By cost categories block: state for which rule panels are open, markup for collapsible rows).
- **Hosted build:** `npm run build:hosted` after UI changes so packaged webui matches.
- **Docs:** Short note in `docs/FEATURES.md` if the dashboard section is documented there.
- **Tests:** Optional lightweight React test or manual QA checklist; no backend/API contract change.
