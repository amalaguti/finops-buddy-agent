## Context

The `finops chat` command initializes the Strands agent by: (1) resolving AWS credentials, (2) creating cost tools, (3) loading MCP clients (Knowledge, Billing, Documentation, Cost Explorer, Pricing), and (4) building the agent. Each step can take 0.5–2 seconds; MCP stdio clients spawn subprocesses and may block. The user sees nothing until the welcome message, which feels unresponsive.

## Goals / Non-Goals

**Goals:**

- Show incremental progress during chat startup so the user knows what is happening.
- Keep implementation simple: wrap existing initialization steps with progress messages.
- Support optional `--quiet` to suppress progress for scripts or minimal-output use cases.

**Non-Goals:**

- Parallelizing MCP loading (would require larger refactor; out of scope).
- Progress bars or spinners (plain text messages are sufficient for CLI).
- Progress for individual tool calls during chat (only startup).

## Decisions

### 1. Progress output target: stderr

**Decision:** Emit progress messages to stderr.

**Rationale:** Keeps stdout clean for agent responses and future piping. Progress is auxiliary feedback, not primary output. Aligns with common CLI practice (e.g. `curl`, `wget`).

**Alternative considered:** stdout — rejected because it would mix with agent output if stdout is captured.

### 2. Message format: short, human-readable lines

**Decision:** One line per step, e.g. `Loading AWS Knowledge MCP...`, `Loading Billing MCP...`, `Ready.`

**Rationale:** Simple, scannable, no fancy formatting. Works in any terminal. Easy to test (capture stderr, assert substring presence).

**Alternative considered:** Spinner or progress bar — rejected; adds dependency and complexity; plain text is sufficient for CLI.

### 3. Progress callback vs inline prints

**Decision:** Use a simple callback (e.g. `progress(msg: str) -> None`) passed into the initialization flow, defaulting to `lambda m: print(m, file=sys.stderr)`.

**Rationale:** Keeps `run_chat_loop` and `build_agent` testable; tests can pass a no-op or capture callback. No global state.

**Alternative considered:** Direct `print(..., file=sys.stderr)` — acceptable but harder to test; callback is cleaner.

### 4. `--quiet` flag placement

**Decision:** Add `--quiet` to the `chat` subparser in `cli.py`. When set, pass a no-op progress callback.

**Rationale:** Matches user expectation for "quiet" mode. Single flag, no new env vars.

## Risks / Trade-offs

- **[Risk]** Progress messages may flicker or appear out of order if stderr is buffered.  
  **Mitigation:** Use `flush=True` on print, or `sys.stderr.flush()` after each message. Most terminals handle this well.

- **[Risk]** Extra output could break scripts that parse stderr.  
  **Mitigation:** `--quiet` flag allows suppression. Document in README.

- **[Trade-off]** Slightly more code in `run_chat_loop` and possibly `build_agent`.  
  **Mitigation:** Keep callback usage minimal; avoid deep changes to MCP creation logic.

## Migration Plan

- No migration. Additive change; existing behavior preserved when `--quiet` is not used.
- Rollback: remove progress calls and `--quiet`; revert to prior behavior.

## Open Questions

- None. Design is straightforward.
