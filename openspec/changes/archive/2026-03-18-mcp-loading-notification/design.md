## Context

The chat API builds the agent and MCP clients on first use (or when the cache is cold). MCP clients are created in sequence in `build_agent_and_tools()` (api/chat.py) by calling `create_*_mcp_client()` for each enabled server. Each call can block for a long time: stdio-based servers use uvx/uv, which may download and install the package on first run (e.g. 30–120+ seconds). The existing progress_callback is invoked for high-level phases ("Preparing agent session", "Preparing system prompt") but not for individual MCP start/ready steps. The FastAPI app logger does not currently log per-MCP progress, and the UI shows only a generic "Working on your request…" until the agent is ready.

## Goals / Non-Goals

**Goals:**

- Give operators visibility: FastAPI (uvicorn) logs SHALL show clear, sequential messages for each MCP loading step (e.g. "Loading MCP: Billing…", "MCP Billing ready").
- Give the UI real-time progress: the chat SSE stream SHALL emit progress events during MCP loading (before the first agent turn) so the client can show which MCP is currently loading.
- Improve UX: the web UI SHALL show a popup (modal or toast) that displays the current MCP loading message and auto-closes when loading finishes.

**Non-Goals:**

- Changing MCP startup order or timeout behavior; no new settings for MCP loading.
- Progress during the agent run (tool_start/tool_end) is already supported and unchanged.
- CLI chat is out of scope for this change (no progress stream in CLI).

## Decisions

1. **Emit MCP progress via existing progress_callback**  
   The chat path already passes a progress_callback into `build_agent_and_tools` and forwards events to the SSE stream. We will call this callback with a dedicated phase (e.g. `mcp_loading`) and a human-readable message (e.g. "Starting Billing MCP server…", "Billing MCP ready") from the same place where we create each MCP client (api/chat.py). No new callback signature or queue.

2. **Log in the same place that emits progress**  
   When building tools in `build_agent_and_tools`, before and after each `create_*_mcp_client()` call we will log at INFO with the app logger (e.g. `logger.info("Loading MCP: Billing…")`, `logger.info("MCP Billing ready")`). This keeps logging and progress text consistent and avoids touching the strands MCP client code.

3. **Phase value `mcp_loading` for SSE**  
   The existing SSE progress event uses `phase` and `message`. We will use `phase: "mcp_loading"` and `message: "<description>"` for MCP steps so the frontend can distinguish MCP loading from other phases (e.g. "phase", "thinking", "heartbeat") and show the popup only during MCP load.

4. **UI: modal or toast for MCP progress**  
   When the chat stream sends a progress event with `phase === "mcp_loading"`, the UI will show a popup (modal or toast) with the message. When the next event is not `mcp_loading` (e.g. "Preparing agent session" or "Preparing system prompt"), the popup is closed. Alternative: always show progress in the existing inline progress area; we choose a dedicated popup so the user cannot miss it during long waits.

5. **No progress from mcp.py create_* functions**  
   The MCP module remains a pure factory: it returns a client or None. The caller (api/chat.py) is responsible for logging and progress_callback around each creation. This avoids passing loggers or callbacks into every create_*_mcp_client and keeps mcp.py independent of the API.

## Risks / Trade-offs

- **Progress only when callback is provided**: Cold build only emits MCP progress when the request path supplies a progress_callback (e.g. POST /chat). Warm-up and cached builds do not go through the progress path; that is acceptable because warm-up is optional and cached builds are fast.
- **Popup might flash for cached builds**: If the agent is already cached, MCP loading is skipped and the UI may briefly show then hide the popup. Mitigation: only open the popup when the first progress event is `mcp_loading`; if the first event is already "Preparing system prompt" or later, do not show the MCP popup.
- **Log volume**: One log line per MCP start and one per ready. With up to ~6 MCPs this is a small number of lines per cold request; acceptable.
