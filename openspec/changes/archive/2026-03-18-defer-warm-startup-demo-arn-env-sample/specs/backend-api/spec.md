# backend-api (delta): Defer warm startup to lifespan

## ADDED Requirements

### Requirement: Agent warm-up runs at ASGI startup only

When agent warm-up is enabled (e.g. `FINOPS_AGENT_WARM_ON_STARTUP` true), the system SHALL run the warm-up (building the chat agent and MCP tool providers) only when the ASGI application starts (e.g. FastAPI lifespan startup), not when the application module is merely imported. This ensures that test runs, scripts, or other code that imports the API module do not trigger MCP initialization and long blocks.

#### Scenario: Warm-up does not run on import

- **WHEN** a process imports the FastAPI app module (e.g. `from finops_buddy.api.app import app`) and does not start the ASGI server
- **THEN** agent warm-up is NOT executed
- **AND** MCP tool providers are not started during that import

#### Scenario: Warm-up runs when server starts

- **WHEN** the ASGI server (e.g. uvicorn) starts the application and warm-up is enabled via settings
- **THEN** the lifespan startup logic runs agent warm-up
- **AND** the first chat request can use the pre-built agent without cold-start delay
