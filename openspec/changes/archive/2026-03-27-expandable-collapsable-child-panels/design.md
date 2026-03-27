## Context

The costs dashboard **By cost categories** block already has a top-level expand/collapse (`costCategoriesExpanded`, default **true**). Inside, **Summary by cost category rule** is a `MiniTable`, followed by one `MiniTable` per category for dimension breakdown. Those per-category tables are always rendered, increasing vertical space.

## Goals / Non-Goals

**Goals:**

- Per-rule **detail** tables are behind a **disclosure** control (button + chevron) consistent with **Savings Plans purchase recommendations** and the outer By cost categories header.
- **Default:** each per-rule panel is **collapsed**; the summary table stays visible without extra clicks.
- **Accessibility:** `aria-expanded` on each disclosure; labels name the cost category rule.

**Non-Goals:**

- Persisting expanded/collapsed state across sessions or page reloads.
- Virtualizing long lists (only collapse behavior).
- Backend or API changes.

## Decisions

1. **State model:** Track **expanded** rule keys (e.g. `Set` of `cat.name` strings, or a `Record<string, boolean>`). Initial state = **none** expanded (all collapsed). Toggling one rule does not affect others.

2. **Pattern:** Reuse the same visual pattern as adjacent sections: full-width `<button>`, title text (rule name), chevron `▼` with `rotate-180` when expanded, then conditional render of the existing `MiniTable` below.

3. **Why not a new `MiniTable` prop:** Collapse is **section** chrome, not cell formatting; wrapping each table keeps `MiniTable` unchanged and avoids prop creep.

4. **Summary table:** Remains **always** rendered when the parent **By cost categories** section is expanded—no extra wrapper.

## Risks / Trade-offs

- **[Risk]** Users may not notice expandable rows → **Mitigation:** Clear chevron + hover state; optional one-line hint in `docs/FEATURES.md` if needed.
- **[Trade-off]** More clicks to see all details vs. shorter default page—intentional per product ask.

## Migration Plan

Deploy with normal frontend build (`npm run build:hosted`); no data migration.

## Open Questions

None.
