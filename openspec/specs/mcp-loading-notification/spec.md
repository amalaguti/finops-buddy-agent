# mcp-loading-notification Specification

## Purpose

Define how the system notifies users and operators during MCP loading: backend logging of each MCP load step, chat stream progress events for MCP loading, and a web UI popup that shows MCP loading progress until the agent is ready.

## ADDED Requirements

### Requirement: Backend logs MCP loading stages

When building the chat agent and MCP tool providers (e.g. in the context of a chat request or warm-up), the backend SHALL log to the application logger (at INFO level) a clear message before starting each MCP server and after each MCP server is ready. Messages SHALL identify the MCP by a short, human-readable name (e.g. Billing, Documentation, Core). Logging SHALL occur in the same code path that creates MCP clients so that operators can see progress in the FastAPI/uvicorn log during long cold starts.

#### Scenario: Log before and after each MCP client creation

- **WHEN** the backend builds the agent and tools and at least one MCP server is enabled
- **THEN** for each MCP server that is being started, the log contains a "loading" message before the client is created and a "ready" (or equivalent) message after the client is created
- **AND** the messages are emitted in sequence so that the log reflects the order of MCP loading

#### Scenario: No MCP loading log when no MCPs enabled

- **WHEN** the backend builds the agent and no MCP servers are enabled
- **THEN** no MCP loading or ready messages are logged for MCP servers

### Requirement: Chat stream emits MCP loading progress events

When the chat endpoint builds the agent and MCP tool providers as part of handling a POST /chat request, the SSE stream SHALL emit progress events for each MCP loading step. Each such event SHALL use a phase value that indicates MCP loading (e.g. `mcp_loading`) and a message that describes the current step (e.g. "Starting Billing MCP server…", "Billing MCP ready"). Events SHALL be emitted before and after each MCP client creation so that the UI can display progress during the entire MCP load phase.

#### Scenario: Stream sends mcp_loading progress during cold build

- **WHEN** a client sends POST /chat and the agent and tools are not cached (cold build) and at least one MCP server is enabled
- **THEN** the stream includes one or more progress events with phase `mcp_loading` and a non-empty message describing the current MCP step
- **AND** these events occur before any progress event for "Preparing system prompt" or "Invoking agent model"

#### Scenario: No mcp_loading events when agent is cached

- **WHEN** a client sends POST /chat and the agent and tools are already cached
- **THEN** the stream need not include any progress event with phase `mcp_loading`
- **AND** the first progress events may be "Preparing agent session" or "Preparing system prompt"

### Requirement: Web UI shows popup during MCP loading

The hosted web UI SHALL display a popup (modal or toast) when the chat stream indicates MCP loading is in progress. The popup SHALL show the current progress message (e.g. "Starting Billing MCP server…"). The popup SHALL be shown when the client receives a progress event with phase `mcp_loading` and SHALL be closed or hidden when the client receives a subsequent progress event that is not `mcp_loading` (e.g. phase "phase" or "thinking") or when the stream ends. The popup SHALL be dismissible or auto-close so that the user is not blocked if the stream stops without a non-mcp_loading event.

#### Scenario: Popup appears when first progress is mcp_loading

- **WHEN** the user sends a chat message and the stream sends a progress event with phase `mcp_loading` and a message
- **THEN** the UI shows a popup that displays that message
- **AND** the user can see that MCP loading is in progress

#### Scenario: Popup closes when MCP loading phase ends

- **WHEN** the popup is visible for MCP loading and the stream then sends a progress event with phase other than `mcp_loading` (e.g. "Preparing system prompt")
- **THEN** the popup is closed or hidden
- **AND** the rest of the chat progress may be shown in the existing inline progress area

#### Scenario: Popup does not show when no mcp_loading events

- **WHEN** the user sends a chat message and the stream never sends a progress event with phase `mcp_loading` (e.g. cached agent)
- **THEN** the MCP loading popup is not shown
- **AND** the UI may show other progress (e.g. "Working on your request…") as today
