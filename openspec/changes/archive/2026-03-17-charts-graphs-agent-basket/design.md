## Context

The FinOps agent uses Strands tools (cost tools, export tools) and MCP clients. Chat responses are markdown; the web UI renders them via ReactMarkdown. Due to data sensitivity, chart generation must be fully local?no external HTTP services. The web UI has a left sidebar (Account, Costs) and a main ChatView; there is no current mechanism to collect or download generated artifacts from the conversation.

## Goals / Non-Goals

**Goals:**

- Agent can generate line, bar, pie, and scatter charts from structured data using matplotlib.
- Charts are embedded inline in agent responses as base64 data URIs (no external URLs).
- Backend can emit `artifact` events in the chat SSE stream for frontend collection.
- Web UI provides an Artifacts basket where users can view, select, and download generated charts.
- All chart data stays in-process; no external chart rendering services.

**Non-Goals:**

- AntV MCP or any external chart service.
- Interactive charts (e.g. Plotly interactive); static PNG output only.
- Geographic or advanced chart types (Sankey, treemap, etc.); those can be added later.
- Persistence of artifacts across page reloads (session-only is acceptable for MVP).

## Decisions

### 1. Chart library: matplotlib

**Choice:** Use matplotlib for chart generation.

**Rationale:** Mature, widely used, no external network calls. Produces PNG/SVG to BytesIO; easy to base64-encode for data URIs. Sufficient for line, bar, pie, scatter?the core FinOps use cases (cost trends, service breakdowns).

**Alternatives considered:** Plotly (richer charts but heavier; kaleido needed for static export). AntV MCP (rejected due to data sensitivity and external cloud).

### 2. Chart tool interface

**Choice:** Single tool `create_chart` with parameters: `chart_type` (line|bar|pie|scatter), `data` (list of dicts, e.g. `[{x, y}]` or `[{label, value}]`), `title` (optional), `x_label` / `y_label` (optional).

**Rationale:** One tool keeps the agent?s tool surface small. The agent already has cost data from other tools; it can shape that into the expected format and call `create_chart`. Return value: markdown string with embedded image `![title](data:image/png;base64,...)` so the agent can include it directly in its reply.

**Alternatives considered:** Separate tools per chart type (e.g. `create_line_chart`, `create_bar_chart`)?more tools, more allow-list entries; rejected for simplicity.

### 3. Artifact event format

**Choice:** Add optional SSE event `artifact` with payload `{ type, title, content }` where `content` is the base64 data URI (or a reference). The frontend appends to its artifacts list and can render a thumbnail.

**Rationale:** Keeps artifact metadata (title, type) separate from the main `message` content. The agent?s reply still contains the inline image; the `artifact` event is for the basket only. Backend emits `artifact` when a chart tool returns successfully?either by inspecting tool results in the chat runner or by having the chart tool itself signal artifacts (e.g. via a callback). Simpler approach: backend inspects the final reply for embedded images and emits artifacts, or the chart tool returns a structured result that the runner can use to emit an artifact. Preferred: chart tool returns markdown; a post-processing step or callback in the agent runner extracts image data URIs from the reply and emits `artifact` events. Alternative: chart tool returns both markdown and a separate ?artifact payload? that the runner forwards. For MVP, we can start with frontend parsing `message` content for `![...](data:...)` patterns to populate the basket, avoiding backend changes initially. Design doc should note both options.

**Refined choice:** Backend emits `artifact` when the chart tool is invoked and returns. The chat runner (or a wrapper around tool execution) can detect chart tool calls and their return value, then emit an `artifact` event with `{ type: "chart", title: "...", content: "data:image/png;base64,..." }`. This requires the runner to have access to the SSE stream or a callback. The API `_stream_chat` runs the agent in a thread; progress is already sent via a queue. We can extend the progress/result flow so that when a tool returns a chart (detected by tool name or return format), we also push an artifact. Implementation: in `run_chat_turn`, when processing tool results, if the tool is `create_chart` and the result contains a data URI, emit an artifact. The streaming path would need to receive this?either `run_chat_turn` returns artifacts as part of its result, or we use a callback. Cleanest: `run_chat_turn` returns `(reply, usage, artifacts)` where `artifacts` is a list of `{ type, title, content }`. The stream generator yields `artifact` events for each item before `message` and `done`. This requires `run_chat_turn` to return artifacts. The chart tool returns markdown; we need to extract the data URI. So: chart tool returns a string like `[CHART_ARTIFACT:title:data:image/png;base64,...]` or a structured dict. Strands tools return strings. We could use a convention: if the string starts with `[CHART_ARTIFACT:`, the runner parses it and emits an artifact, then strips it for the agent?s reply. Or the tool returns JSON: `{"markdown": "...", "artifact": {"type":"chart","title":"...","content":"..."}}`. But Strands tools typically return strings. Simpler: the tool returns only the markdown. The runner parses the final reply for `![...](data:image/png;base64,...)` and emits one artifact per match. That way we don?t need to change the tool return format. So: **backend parses the assistant reply for embedded data URI images and emits `artifact` events for each**. No tool interface change. Runner/stream logic does a quick regex on the reply before sending `message`.

### 4. Artifacts basket placement

**Choice:** Place the Artifacts basket in the **top navbar** (preferred) or as a **right-side panel** (e.g. dropdown or expandable area). Artifacts do not persist (session-only). When empty, show a compact "No artifacts yet" state. When populated, list items with thumbnail and download button.

**Rationale:** Top navbar keeps artifacts visible and accessible without competing with Account/Costs context in the left sidebar. Right-side panel is an alternative if navbar space is limited. Session-only avoids persistence complexity.

**Alternatives considered:** Left sidebar (rejected?user prefers navbar or right panel). Floating basket icon (more discoverability work).

### 5. Image rendering in ChatView

**Choice:** Add an `img` component to ReactMarkdown?s `components` prop. Allow `src` to be `data:` URIs and optionally same-origin URLs. Apply max-width, rounded corners, and shadow for readability.

**Rationale:** ReactMarkdown supports `img` by default, but we want consistent styling. Restricting to data URIs and same-origin avoids arbitrary external image loading (security).

## Risks / Trade-offs

| Risk | Mitigation |
|------|-------------|
| matplotlib adds ~50MB to install | Acceptable for desktop/server use; document in README |
| Large base64 in SSE could bloat stream | Artifact event carries content; consider max size or ?artifact available? with fetch later; for MVP, inline is fine |
| Parsing reply for images is brittle | Use a simple regex for `![...](data:image/png;base64,...)`; document format; add tests |
| Basket grows large in long sessions | Add ?Clear? action; optionally cap display (e.g. last 20); no persistence so refresh clears |

## Migration Plan

- Add matplotlib to `pyproject.toml`; run `poetry lock` and `poetry install`.
- Implement chart tool; add to agent builder and read-only allow-list.
- Extend chat runner/stream to parse reply and emit `artifact` events.
- Update frontend: ArtifactsBasket component, ChatView `img` handling, navbar or right-panel integration.
- No database or config migration required for MVP.
- Rollback: remove chart tool from allow-list; frontend ignores `artifact` events (no crash).

## Open Questions

- Should artifact events be emitted for images in *all* assistant messages (e.g. past history) or only the current turn? **Recommendation:** Only current turn to avoid re-processing history.
- DPI/format: Use default matplotlib DPI (100) or make configurable? **Recommendation:** Default 100; add optional `chart_dpi` in settings if needed later.
