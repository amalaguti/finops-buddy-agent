## Why

MCP servers run as **subprocesses** (`uvx`). A **crash or hang** mid-conversation currently lacks a **health boundary**: the agent may **block** or fail with **opaque errors**. Startup probing exists but is **not** a per-request or continuous **circuit breaker** with **graceful degradation** (e.g. continue chat with Cost Explorer tools when Billing MCP is down).

## What Changes

- **Per-invocation or periodic health** checks for MCP clients with **timeouts**.
- **Circuit breaker** state per MCP server (open/half-open) with metrics-friendly logging.
- **Degraded mode**: when an MCP is unavailable, the agent **SHALL** surface a clear user-visible message and **SHALL** avoid infinite retries; optional fallback to **built-in** AWS tools where spec allows.
- Configuration via **`FINOPS_*`** and settings YAML (timeouts, breaker thresholds).

## Capabilities

### New Capabilities

- `mcp-runtime-resilience`: Health checks, timeouts, circuit breaking, and degradation behavior for MCP subprocess clients.

### Modified Capabilities

- `chat-agent`: Tool assembly respects degraded MCP availability.
- Relevant MCP capability specs (`mcp-billing-cost`, `mcp-core-server`, etc.) as needed for fallback wording.

## Impact

- `src/finops_buddy/agent/mcp.py` (or equivalent), agent builder, tests simulating subprocess failure.
