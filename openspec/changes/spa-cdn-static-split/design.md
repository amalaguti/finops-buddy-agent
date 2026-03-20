## Context

**Same-origin** cookies for OIDC **may** favor **one host** for UI + API; CloudFront can **front both** S3 and ALB origin with path-based routing to preserve origin semantics.

## Goals / Non-Goals

**Goals:** Reference architecture for **path or host** routing; clear **env vars** for frontend API base and **CORS** if cross-origin.

**Non-Goals:** Mandate CDN for all users; break local `finops serve` defaults.

## Decisions

| Pattern | Notes |
|---------|------|
| CloudFront: `/` → S3, `/api` → ALB | Single site cookie domain if configured carefully. |
| Two hostnames | `app.` + `api.`; may need CORS + CSRF review. |

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| OIDC redirect URI mismatch | Register **both** or single CloudFront URL only. |
| Stale cached JS | Versioned asset names (Vite hash) + `Cache-Control`. |

## Migration Plan

Phase 1: documentation + flag to **skip** embedded static. Phase 2: pipeline upload.

## Open Questions

- Whether **Content-Security-Policy** is owned by CloudFront or S3 website config.
