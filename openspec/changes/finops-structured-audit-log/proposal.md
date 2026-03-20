## Why

For **multi-account FinOps** data, **HTTP access logs** alone are insufficient for governance: reviewers need **structured audit events** tying **authenticated identity** to **data-plane actions** (which **account/target**, which **endpoint**, which **MCP tools** invoked, outcome). The `deploy-aws` doc mentions audit lines; current middleware is **generic HTTP logging**, not **FinOps audit events**.

## What Changes

- Emit **structured JSON** (or ECS-friendly single-line) audit records for **sensitive operations**: cost/dashboard reads, context/profile resolution in cloud mode, chat tool invocations (names + target account id, **not** full prompts if policy forbids).
- Correlate with **request id** and **OIDC subject** (when trusted proxy auth is on).
- Configurable **sink**: stdout (default), future S3/CloudWatch Logs subscription (document only or optional flag).
- **Never** log secrets, raw tokens, or full message bodies unless explicitly allowed by policy flag (default off).

## Capabilities

### New Capabilities

- `structured-finops-audit`: Schema and emission rules for FinOps audit events.

### Modified Capabilities

- `backend-api`: Audit hooks on selected routes and agent tool boundary.

## Impact

- FastAPI middleware / dependencies, agent hooks, log pipeline docs, retention guidance.
