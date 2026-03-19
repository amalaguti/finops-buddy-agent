# backend-api Specification (delta)

## Purpose

Defines the HTTP API layer for the FinOps Agent: read-only endpoints (profiles, context, costs) and chat with streaming, in single-user mode. This delta adds MCP loading progress and logging.

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
