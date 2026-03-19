## Why

When the user runs `finops chat`, the CLI spends several seconds initializing before showing the first prompt: resolving AWS credentials, creating cost tools, and loading MCP servers (Knowledge, Billing, Documentation, Cost Explorer, Pricing). During this time the user sees nothing, which feels like the app is frozen or unresponsive. Showing progress during startup improves perceived responsiveness and sets clear expectations.

## What Changes

- Display incremental progress messages during chat startup (e.g. "Resolving credentials...", "Loading AWS Knowledge MCP...", "Loading Billing MCP...", etc.).
- Progress messages SHALL appear on stderr (or stdout) as each step starts or completes, so the user knows what is happening.
- Optionally support a `--quiet` flag to suppress startup progress (for scripts or users who prefer minimal output).
- No change to the underlying initialization logic—only add progress reporting around existing steps.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `chat-agent`: Add requirement that the chat subcommand SHALL display startup progress so the user is informed during initialization (credentials, cost tools, MCP servers, agent build).

## Impact

- **Code**: `src/finops_agent/agent/runner.py` (`run_chat_loop`, possibly `build_agent`), `src/finops_agent/cli.py` (optional `--quiet` for chat).
- **UX**: Users see progress during the 2–5 second startup instead of a blank screen.
- **Config**: Optional `--quiet` flag; no new settings or env vars required for basic progress.
