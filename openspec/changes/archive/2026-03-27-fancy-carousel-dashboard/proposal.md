## Why

Operators and stakeholders often view the costs dashboard on a shared screen or wall display. The current dense grid shows every table at once, which is hard to read at a distance. A **carousel presentation mode** cycles one block at a time with a modern 3D-style layout and configurable dwell time so each dataset gets full attention.

## What Changes

- Add a **carousel mode** toggle on the hosted costs dashboard (`DashboardSection`) that replaces the default grid with a **3D-style carousel** of dashboard blocks.
- **One slide per `MiniTable`**, plus **one slide for the Savings Plans summary** panel (the utilization/coverage card, which is not a `MiniTable`), so **all primary dashboard blocks** participate in the rotation.
- **Auto-advance** with a default of **15 seconds** and a dropdown to choose **10 / 15 / 30** seconds.
- **Include** the **By cost categories** and **Savings Plans purchase recommendations** content in the slide list: when carousel mode is on, treat those sections as **expanded** for rotation so every nested `MiniTable` is a slide (summary + per-category detail tables + purchase recommendations table).
- **Exclude** ephemeral drill-down / detail overlays (recommendation, account, service, anomaly, Savings Plans details modal) from the carousel sequence; they remain available in normal interaction outside carousel or when carousel is off (see design).
- **Accessibility**: Respect **`prefers-reduced-motion`** (no auto-advance; optional simplified transition). Provide **pause** control for auto-rotating content.
- **Frontend-only**; no new backend APIs or Python changes.

## Capabilities

### New Capabilities

- `costs-dashboard-carousel`: Hosted UI behavior for carousel presentation mode, slide composition, interval control, reduced motion, and pause.

### Modified Capabilities

- None (no changes to `costs-dashboard-lookback` or other server-side specs).

## Impact

- **Code**: `frontend/src/components/DashboardSection.jsx` (and possibly a small extracted component under `frontend/src/components/`). Rebuild hosted web UI (`npm run build:hosted`) when implementing.
- **Tests**: Frontend tests if the project already tests this component; otherwise lightweight tests for slide list / interval helpers if extracted.
- **Dependencies**: Prefer **no** new npm packages unless justified in `design.md` (CSS-first 3D carousel).
