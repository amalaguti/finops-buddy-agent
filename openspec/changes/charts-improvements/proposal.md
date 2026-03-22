## Why

Agent-generated charts use matplotlib defaults and a low export DPI (`dpi=100`), so output looks plain and can appear soft when scaled in the web UI. Improving **stylesheet defaults** and **render parameters** (resolution, figure size, margins) raises perceived quality without changing the transport (PNG data URI in markdown) or adding interactive chart stacks.

## What Changes

- Apply a **consistent matplotlib style** (built-in stylesheet and/or `rcParams`) before drawing in `create_chart`.
- Tune **raster export**: higher default DPI, explicit default figure size, and **tight save** options so charts use space efficiently in chat.
- For **bar** charts only, **sort categories by value descending** so typical FinOps “top services / top accounts” views read naturally (stable ordering on ties).
- Extend **pytest** coverage for new spec scenarios; no new runtime dependencies (matplotlib only, as today).

## Capabilities

### New Capabilities

- None (behavior stays within existing chart-generation scope).

### Modified Capabilities

- `chart-generation`: Add normative requirements for default styling, export quality, and bar-chart sort order. Tool contract (`create_chart` signature, PNG data URI markdown, chart types, allow-list, no network) remains unchanged.

## Impact

- **Code:** `src/finops_buddy/agent/chart_tools.py` (primary); possibly small prompt tweaks in `chat_loop.py` only if we want the model to rely on server-side sort (optional, likely unnecessary).
- **Tests:** `tests/test_chart_tools.py` (new scenarios).
- **Specs:** Delta under this change; after apply, sync into `openspec/specs/chart-generation/spec.md`.
- **Dependencies:** None new.
- **Frontend:** None (still embedded PNG).
- **User configuration:** None required for the first iteration (defaults live in code; optional `FINOPS_*` overrides can be a follow-up change if needed).
