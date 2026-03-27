## Context

The costs dashboard is implemented in `frontend/src/components/DashboardSection.jsx` as a responsive grid of `MiniTable` components plus a Savings Plans summary card and collapsible sections for cost categories and Savings Plans purchase recommendations. This change adds an alternate **presentation layout** without changing backend APIs or data fetching behavior.

## Goals / Non-Goals

**Goals:**

- Toggle **carousel mode** in the costs dashboard area with a **3D-forward** visual (perspective, depth, smooth transitions) using **CSS-first** styling aligned with existing `finops-*` theme tokens.
- **One slide per `MiniTable`**, plus **one slide** for the **Savings Plans summary** card (utilization/coverage block).
- **Include all primary blocks**: main grid tables, Savings Plans summary, cost categories (summary `MiniTable` + each category’s **Details** `MiniTable`), and the **Purchase recommendations** `MiniTable`.
- **Interval**: default **15 s**; user-selectable **10 / 15 / 30** seconds via dropdown.
- **Accessibility**: `prefers-reduced-motion` disables auto-advance (and may use instant or minimal transitions); visible **Pause / Play** (or equivalent) for the auto-rotating carousel.
- Optional **persist** carousel mode + interval in `localStorage` (keys scoped to this UI, e.g. `finops-costs-carousel-*`) so kiosk users keep preferences—implementation may defer persistence to tasks if timeboxed.

**Non-Goals:**

- New REST APIs, env vars, or `config/settings.yaml` entries (purely client-side UI).
- Rotating **drill-down overlays** (recommendation/account/service/anomaly detail panels, expanded Savings Plans details modal)—these stay manual interactions; carousel applies to the **primary** dashboard blocks only.
- Adding new npm carousel libraries unless a clear gap appears; prefer composable React state + CSS transforms.

## Decisions

### 1. Slide list construction

**Decision:** Build an **ordered slide registry** that mirrors the visual order of primary content:

1. By AWS service (`MiniTable`)
2. By linked account (`MiniTable`)
3. Marketplace (`MiniTable`)
4. Optimization recommendations (`MiniTable`)
5. Anomalies (`MiniTable`)
6. Savings Plans **summary** panel (non-table slide)
7. Cost category **summary** (`MiniTable`)
8. For each cost category in loaded data: **Details** `MiniTable` (one slide per category)
9. Savings Plans **purchase recommendations** (`MiniTable`)

**Rationale:** Matches “Option A” (one slide per `MiniTable`) while including the non-table Savings Plans block (“all blocks”). Nested category tables are each their own slide.

**Alternatives:** Group multiple tables per slide—rejected per product choice.

### 2. Collapsible sections in carousel mode

**Decision:** When carousel mode is **on**, **force-expand** the “By cost categories” and “Savings Plans purchase recommendations” sections so all slides in (7)–(9) exist in the DOM and can be focused visually. When carousel mode is **off**, restore prior expand/collapse behavior (or keep expanded state in user-controlled toggles independent of carousel).

**Rationale:** Avoids empty or skipped slides and matches “include all blocks.”

### 3. 3D carousel implementation

**Decision:** Use a **single active slide** with CSS `perspective`, `transform` (e.g. translate/rotateY or scale), and theme-consistent shadows. Optionally show **adjacent slide previews** at lower opacity for depth; avoid heavy JS physics.

**Alternatives:** Swiper/Embla—only add if CSS approach is insufficient for smoothness.

### 4. Timer and interaction

**Decision:** `setInterval` or `setTimeout` chain for auto-advance; **reset timer** when the user changes interval, navigates manually (if prev/next added), or toggles pause. **Pause** while the user focuses a focusable control inside the active slide (optional but recommended) or rely on explicit Pause only—pick one in implementation; spec requires at least pause control + reduced motion.

### 5. Build output

**Decision:** After UI changes, run `frontend` `npm run build:hosted` so `src/finops_buddy/webui/` embeds the updated bundle.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Large `DashboardSection.jsx` grows further | Extract `CostsDashboardCarousel` (or similar) into `frontend/src/components/` |
| Many slides when many cost categories | Accept long cycles; optional future: cap or group (out of scope) |
| Auto-rotation vs WCAG 2.2.2 | Pause control + respect `prefers-reduced-motion` |
| Forced expand may surprise users | Only when carousel is on; turning carousel off returns to normal collapses |

## Migration Plan

- Ship with frontend only; no DB or API migration.
- Rollback: revert UI commit and rebuild hosted assets.

## Open Questions

- Whether to add **manual** prev/next arrows in v1 (recommended for accessibility and debugging); can be a small follow-up if omitted.
