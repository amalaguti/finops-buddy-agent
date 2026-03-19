## Why

The FinOps agent conversations frequently involve cost data and trends. Users benefit from visual charts and graphs embedded in the analysis rather than tables alone. Due to data sensitivity, chart generation must stay fully local—no external services or cloud rendering. Additionally, users need a way to collect and download generated artifacts (charts, reports) from the conversation, with a dedicated UI area to pick and choose what to keep.

## What Changes

- Add a **Python-native chart generation tool** for the agent: line, bar, pie, and scatter charts using matplotlib. The agent can invoke this tool with cost data and receive a base64-encoded image to embed in its markdown response. All processing stays in-process; no external HTTP calls.
- Extend the **chat SSE stream** with an optional `artifact` event so the backend can signal generated charts/reports for collection.
- Add an **Artifacts basket** to the web UI: placed in the top navbar (preferred) or as a right-side panel (e.g. dropdown or expandable area). Lists generated charts and reports from the conversation. Users can preview, select, and download individual items or all at once. Artifacts do not persist across page reloads (session-only).
- Update **ChatView** markdown rendering to support embedded images (including data URIs) with appropriate styling.
- Add **matplotlib** (and optionally **numpy**) to `pyproject.toml` as runtime dependencies.

## Capabilities

### New Capabilities

- `chart-generation`: Agent tool that generates charts (line, bar, pie, scatter) from structured data using matplotlib. Returns base64 data URI for inline embedding. Fully local; no external services.
- `artifacts-basket`: Web UI component that collects generated artifacts (charts, reports) from the conversation, displays them in the top navbar or right-side panel, and allows users to download selected items. Session-only; no persistence.

### Modified Capabilities

- (none)

## Impact

- **Dependencies**: `matplotlib>=3.7` (and optionally `numpy`) in `pyproject.toml`.
- **Agent**: New tool in `finops_buddy.agent.tools` (or dedicated module); tool added to read-only allow-list.
- **Backend API**: Optional `artifact` SSE event in `/chat` stream; no breaking changes to existing events.
- **Frontend**: New ArtifactsBasket component; navbar or right-panel integration; ChatView markdown `img` handling.
- **Settings**: Optional `config/settings.yaml` entries for chart defaults (e.g. DPI, format) if needed.
