## Why

Embedding the **compiled SPA** inside the Python package (`src/finops_buddy/webui/`) is **pragmatic** for **desktop and single-binary** distribution. For **cloud ECS**, serving static assets from **Fargate** works but is **not optimal**: **CloudFront + S3** (or CloudFront → ALB split) reduces **compute cost**, improves **caching**, and separates **release cadence** of UI vs API. The frontend already supports **`VITE_API_BASE`** for API URL; the **repo packaging choice** should be documented as a **trade-off** with a **clear split path**.

## What Changes

- **Document** the **split deployment** pattern: static bucket + CloudFront, API-only tasks behind ALB path `/api` or separate host.
- **Optional implementation**: build pipeline artifacts (zip to S3), **disable** static mount in API when `FINOPS_SERVE_STATIC_UI=false` (example flag), health check paths.
- **IaC guidance** for ACM, OAI/OAC, cache behaviors, and **security headers**.

## Capabilities

### New Capabilities

- `spa-cdn-delivery`: Requirements for optional CDN/S3 static hosting alongside API-only container.

### Modified Capabilities

- `hosted-web-ui`: Build-time and runtime expectations when API does not serve `index.html`.
- `docker-deployment`: Document image variants or env for API-only mode.

## Impact

- CI/CD, `finops serve` static file logic, docs; no forced migration from embedded SPA.
