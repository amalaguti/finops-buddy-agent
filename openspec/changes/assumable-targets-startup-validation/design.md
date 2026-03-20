## Context

Use **STS AssumeRole** with **DurationSeconds** minimum allowed (often 900s — confirm AWS minimum; if too long for “probe”, use **GetCallerIdentity** after assume or use a dedicated **validation-only** action if org permits). Alternative: **IAM SimulatePrincipalPolicy** (different permission set).

## Goals / Non-Goals

**Goals:** Detect **AccessDenied** / **invalid ARN** before user traffic.

**Non-Goals:** Prove every Cost Explorer call succeeds (only trust + base session).

## Decisions

| Approach | Notes |
|----------|-------|
| AssumeRole + immediate **GetCallerIdentity** on assumed creds | Strong signal; consumes STS quota. |
| Strict vs warn | `FINOPS_ASSUMABLE_TARGETS_VALIDATE_STRICT` |

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| STS throttle | Batch + jitter; cache validation result for N minutes. |

## Migration Plan

Default **warn** mode first; **strict** for production after burn-in.

## Open Questions

- Minimum **DurationSeconds** acceptable to security for probe credentials.
