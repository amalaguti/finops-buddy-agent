## ADDED Requirements

### Requirement: Startup progress display

The chat subcommand SHALL display incremental progress messages during initialization so the user is informed while credentials are resolved, cost tools are created, MCP servers are loaded, and the agent is built. Progress messages SHALL be emitted to stderr. Each major step (e.g. resolving credentials, loading each MCP server, building agent) SHALL produce a short, human-readable message (e.g. "Resolving credentials...", "Loading AWS Knowledge MCP...", "Ready."). The CLI SHALL support an optional `--quiet` flag on the chat subcommand; when `--quiet` is set, the CLI SHALL NOT display startup progress messages.

#### Scenario: Progress shown during chat startup

- **WHEN** the user runs `finops chat` (without `--quiet`) and initialization begins
- **THEN** the CLI emits progress messages to stderr for each major step (e.g. credentials, cost tools, MCP servers, agent build) before displaying the welcome message and prompt

#### Scenario: Progress includes MCP server names when loading

- **WHEN** the user runs `finops chat` and one or more MCP servers are enabled (e.g. AWS Knowledge, Billing, Documentation)
- **THEN** the CLI emits a progress message for each MCP server as it is loaded (e.g. "Loading AWS Knowledge MCP...", "Loading Billing MCP...")

#### Scenario: Quiet mode suppresses startup progress

- **WHEN** the user runs `finops chat --quiet` (or `finops chat -q` if short form is supported)
- **THEN** the CLI does not emit startup progress messages to stderr; the user sees only the welcome message and prompt once initialization completes
