# MCP loading notification

## Why

The first chat request (or any request that builds the agent and MCP clients) can take a long time because MCP servers are started via stdio (e.g. uvx) and may trigger download/install on first run. Users see no feedback during this period: the backend blocks without logging, and the UI shows only a generic "Working on your request…" until the agent is ready. This leads to confusion and the impression that the app is stuck.

## What Changes

- **Backend logging**: The FastAPI process SHALL log clear, sequential messages during MCP loading (e.g. "Loading MCP: Billing…", "MCP Billing ready") so operators and developers can see progress in the API log.
- **Streaming progress**: The chat SSE stream SHALL emit progress events specifically for MCP loading phases (e.g. phase `mcp_loading` with a message such as "Starting Billing MCP server…") so the UI can show MCP-specific progress before the agent runs.
- **UI popup**: The web UI SHALL show a popup (modal or toast) during MCP loading that displays the current MCP loading message and keeps the user informed until loading completes. The popup SHALL be dismissible or auto-close when loading finishes.

## Capabilities

### New Capabilities

- `mcp-loading-notification`: Backend logging of MCP load stages, chat stream progress events for MCP loading, and UI popup/modal to display MCP loading progress to the user.

### Modified Capabilities

- `backend-api`: Chat streaming requirement is extended so that the server emits progress events during MCP loading (before the first agent turn) and the backend logs each MCP loading stage to the application log.

## Impact

- **Code**: `src/finops_buddy/api/chat.py` (build_agent_and_tools, progress callback during MCP creation), `src/finops_buddy/agent/mcp.py` (optional: logging hooks or callbacks), `src/finops_buddy/api/app.py` (no change to SSE format beyond new phase/message values). Frontend: chat component and a new popup/modal component or toast for MCP progress.
- **APIs**: Chat SSE `progress` event already supports `phase` and `message`; new phase value `mcp_loading` (or similar) and messages like "Starting Billing MCP server…" will be used. No new endpoints.
- **Dependencies**: None.
- **Systems**: Operators get better visibility in FastAPI logs; users get clear in-UI feedback during long MCP startup.
