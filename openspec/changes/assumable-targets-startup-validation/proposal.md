## Why

`FINOPS_ASSUMABLE_TARGETS_JSON` (and YAML map) defines **role ARNs** the task role must **AssumeRole** into. **Trust policy drift** or **typos** are often discovered **at query time** mid-chat. A **startup validation** (dry-run `sts:AssumeRole` with **short duration**) surfaces **misconfiguration early** at deploy time or process start.

## What Changes

- On startup (or async background after start) when **cloud deployment mode** and a **non-empty** target map are configured, the system SHALL **attempt validation** of each target role (documented: sequential or parallel with cap).
- Outcomes: **log + metric** for success; **fail fast** or **degraded warning** based on `FINOPS_*` strict flag.
- Respect **rate limits** (backoff, max concurrent checks).

## Capabilities

### New Capabilities

- `assumable-role-startup-validation`: Normative behavior for validating configured assume-role targets at startup.

### Modified Capabilities

- `aws-identity`: Integrate validation with session/role map loading.
- `app-settings`: Config keys for strict/warn mode and validation enable.

## Impact

- Startup time / STS API usage; clear operator runbooks.
