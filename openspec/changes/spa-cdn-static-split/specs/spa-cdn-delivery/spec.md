# spa-cdn-delivery Specification

## Purpose

Allow **optional** hosting of the **compiled web UI** on **S3 + CloudFront** (or equivalent CDN) while the **FastAPI** container serves **API and chat** only, for **cost and caching** benefits in cloud deployment.

## ADDED Requirements

### Requirement: API-only mode disables bundled static UI serving

The system SHALL support an **API-only** mode (via `FINOPS_*` and/or YAML) where the FastAPI application **does not** serve the embedded **compiled SPA** (`index.html`, hashed assets) and **only** exposes API routes (including health). When API-only mode is off, existing **single-origin** behavior SHALL remain unchanged.

#### Scenario: API-only returns 404 for root document

- **WHEN** API-only mode is enabled and a client requests `GET /` expecting the SPA
- **THEN** the response is **404** or a documented minimal response that is **not** the full SPA shell

### Requirement: Documented CloudFront + S3 + ALB reference pattern

The project SHALL document a **reference pattern** for CloudFront with **at least two origins**: **S3** (static UI) and **ALB** (API), including **path or behavior** routing (e.g. `/api/*` to ALB). The documentation SHALL mention **TLS**, **ACM certificate** placement, and **cache invalidation** on UI deploy.

#### Scenario: Operator finds routing table

- **WHEN** a reader opens the CDN deployment section
- **THEN** the document states which paths go to S3 vs API origin

### Requirement: Frontend API base configuration remains supported

The SPA build SHALL continue to support **`VITE_API_BASE`** (or documented successor) so a UI served from a **different origin** can reach the API. README SHALL describe **CORS** requirements when API and UI origins differ.

#### Scenario: Cross-origin API calls documented

- **WHEN** UI and API are on different hostnames
- **THEN** README lists required **CORS** settings on FastAPI for browser chat and REST

### Requirement: No breakage for embedded package workflow

Default **Poetry package** and **Docker** image behavior for local users SHALL **continue** to include and serve the embedded web UI unless the user explicitly selects API-only artifacts per documented build target.

#### Scenario: Default docker image still serves UI

- **WHEN** a user runs the default container image without API-only flags
- **THEN** the web UI is available from the container as today
