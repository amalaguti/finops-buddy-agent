## 1. Setup

- [x] 1.1 Create feature branch `feature/charts-graphs-agent-basket` (never implement on main)
- [x] 1.2 Add `matplotlib>=3.7` to `pyproject.toml` under `[tool.poetry.dependencies]`; run `poetry lock` and `poetry install`

## 2. Chart Tool Implementation

- [x] 2.1 Create `create_chart` tool in `finops_buddy.agent.tools` (or new module `finops_buddy.agent.chart_tools`): accepts `chart_type` (line|bar|pie|scatter), `data` (list of dicts), `title` (optional), `x_label`/`y_label` (optional); returns markdown string with embedded `![title](data:image/png;base64,...)` or error message on invalid data
- [x] 2.2 Add `create_chart` to the agent builder (e.g. `create_cost_tools` or separate `create_chart_tools`) and pass to `Agent(tools=...)`
- [x] 2.3 Add `create_chart` to the default read-only allow-list in settings/default tool allow-list so the tool executes when the agent invokes it

## 3. Backend Artifact Events

- [x] 3.1 Add helper to parse assistant reply for embedded data URI images: regex for `![...](data:image/png;base64,...)`; return list of `{ type, title, content }`
- [x] 3.2 Extend `run_chat_turn` (in `api/chat.py`) to return `(reply, usage, artifacts)` where `artifacts` is the parsed list from the reply
- [x] 3.3 Update `_stream_chat` in `app.py` to yield `artifact` SSE events for each artifact before the `message` event; ensure existing `progress`, `message`, `done`, `error` events remain unchanged

## 4. Frontend ChatView and Image Rendering

- [x] 4.1 Add `img` component to ReactMarkdown `components` in `ChatView.jsx`: allow `data:` URIs; restrict or block non-data, non-same-origin URLs; apply max-width, rounded corners, shadow for styling
- [x] 4.2 Update `streamChat` in `api/chat.js` to handle `artifact` event: add artifact to a callback or return it so the parent can update state

## 5. Artifacts Basket UI

- [x] 5.1 Create `ArtifactsBasket` component: collapsible section, shows "No artifacts yet" when empty; lists artifacts with thumbnail and download button; supports "Download all"
- [x] 5.2 Add ArtifactsBasket to the top navbar (preferred) or as a right-side panel—e.g. "Artifacts" button in header that opens dropdown/panel; do not add to left sidebar
- [x] 5.3 Wire ChatView to ArtifactsBasket: pass artifacts from chat stream (artifact events) into basket state; implement download (single and all) for data URI content as PNG files with sensible names

## 6. Quality and Tests

- [x] 6.1 Run `poetry run ruff check .` and `poetry run ruff format .`; fix any issues
- [x] 6.2 Run `poetry run bandit -c pyproject.toml -r src/`; fix any medium+ severity findings
- [x] 6.3 Add pytest tests for chart tool: `test_create_chart_returns_line_chart_markdown`, `test_create_chart_returns_bar_chart_markdown`, `test_create_chart_returns_pie_chart_markdown`, `test_create_chart_returns_scatter_chart_markdown`, `test_create_chart_on_allow_list`, `test_create_chart_handles_invalid_data`, `test_create_chart_no_network_calls`
- [x] 6.4 Add pytest tests for artifact parsing: `test_parse_reply_extracts_data_uri_images`, `test_parse_reply_returns_empty_when_no_images`
- [x] 6.5 Run `poetry run pip-audit`; address any vulnerabilities with available fixes

## 7. Documentation

- [x] 7.1 Update README.md: document that chart generation uses matplotlib (local, no external services); add brief note on Artifacts basket in the web UI section
- [x] 7.2 If chart-related settings are added (e.g. `chart_dpi`), update `config/settings.yaml` template with commented placeholder
