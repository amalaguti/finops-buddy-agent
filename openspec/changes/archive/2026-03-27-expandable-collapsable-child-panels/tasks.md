# expandable-collapsable-child-panels — Tasks

**Branch:** Implement on a feature branch (e.g. `feature/expandable-collapsable-child-panels`), not on `main`.

## 1. Frontend — collapsible per-rule panels

- [x] 1.1 In `frontend/src/components/DashboardSection.jsx`, keep **Summary by cost category rule** as the first block inside the expanded **By cost categories** section (unchanged).
- [x] 1.2 Wrap each per-category `MiniTable` (detail rows) in a disclosure control: full-width button with rule title + chevron, `aria-expanded`, matching other dashboard collapsibles; render the `MiniTable` only when that rule’s panel is expanded.
- [x] 1.3 Track expanded state so **no** rule is expanded initially (all detail panels **collapsed by default**). Toggling one rule does not collapse others unless you intentionally choose a single “accordion” behavior (design: independent toggles).
- [x] 1.4 Run **`cd frontend && npm run build:hosted`** so `src/finops_buddy/webui/` is updated.

## 2. Documentation

- [x] 2.1 Add a short note to **`docs/FEATURES.md`** (cost categories / dashboard) that per-rule detail tables are collapsible and collapsed by default.

## 3. Verification (no API or settings change)

- [x] 3.1 Manually verify the **delta spec scenarios** in `specs/cost-categories-dashboard/spec.md` (summary visible, details collapsed by default, expand/collapse per rule). Pure UI: mapping to pytest is not practical without a frontend test harness; regression coverage is manual for this change.
- [x] 3.2 Run **`poetry run ruff check .`** and **`poetry run ruff format .`**; fix any issues in touched files.
- [x] 3.3 Run **`poetry run bandit -c pyproject.toml -r src/`**; fix medium+ findings.
- [x] 3.4 Run **`poetry run pytest`** until green.
- [x] 3.5 Run **`poetry run pip-audit`**; address or document per project policy.

## 4. OpenSpec sync (on apply)

- [x] 4.1 After implementation, merge **`openspec/changes/expandable-collapsable-child-panels/specs/cost-categories-dashboard/spec.md`** delta into **`openspec/specs/cost-categories-dashboard/spec.md`**.
