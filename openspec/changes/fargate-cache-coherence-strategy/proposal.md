## Why

On **ECS Fargate with multiple tasks**, **in-memory** caches (profile→account mapping, warmed agent fragments, etc.) are **per-task**. The `deploy-aws` design implies scale-out but does not **explicitly** state the **consistency model**: **cold cache per task**, **eventual** alignment, or a **shared cache** (ElastiCache/Redis). Operators need a **documented decision** and optional implementation path to avoid surprise latency or divergent behavior across tasks.

## What Changes

- **Document** the chosen strategy: accept **per-task cold state**, or adopt **shared cache** for specific keys (with TTL and security).
- If shared cache is in scope: define **what** is cached (non-secret derived mappings), **encryption**, **VPC placement**, and **invalidation**.
- Metrics guidance: cache hit rate, warm-up duration per task after deploy.

## Capabilities

### New Capabilities

- `multi-instance-runtime-cache`: Requirements for cache coherence across Fargate tasks (documentary + optional Redis).

### Modified Capabilities

- `backend-api` / `aws-identity` (if mapping cache behavior changes): reference cache source of truth.

## Impact

- Docs, optional Terraform for Redis, `finops_buddy` cache layer abstraction, no user-facing API break unless explicitly added.
