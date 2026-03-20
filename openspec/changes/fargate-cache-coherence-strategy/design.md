## Context

**Sticky sessions** help SSE but **do not unify** server-side caches. Two users on two tasks may see **different mapping freshness** unless a shared store or external source of truth is used.

## Goals / Non-Goals

**Goals:** Clear **SLO statement**: e.g. “each task may cold-start mapping; max staleness N minutes if Redis enabled.”

**Non-Goals:** Distributed session store for chat history (separate change).

## Decisions

| Strategy | When to pick |
|----------|----------------|
| **A: Per-task only** | Small teams, low task count, accept redundant STS/config reads at warm-up. |
| **B: Redis for derived mappings** | Many tasks, need stable profile→account map without hammering IdP/files. |

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Redis becomes critical infra | Multi-AZ, auth token via Secrets Manager, TLS. |
| Caching sensitive data | Cache only **non-secret** ids; short TTL. |

## Migration Plan

Phase 1: documentation + metrics. Phase 2: optional Redis behind feature flag.

## Open Questions

- Whether mapping in **cloud mode** comes from **SSM/Parameter Store** instead of file cache (overlaps `deploy-aws`).
