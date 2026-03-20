## Context

FinOps Buddy is a **FastAPI + uvicorn** application with **SSE** (and WebSocket-capable) chat, **Strands** agent with **OpenAI and/or Bedrock**, and **boto3** for AWS Cost Explorer and related APIs. Today, **AWS profile names** come from the shared config file and **API auth is effectively none** (single-user, credentials from env/files). The target environment is **internal employees only**, but the service is **reachable from the public internet** (no VPN/PrivateLink in v1), so **sensitive FinOps data** requires **strong edge controls** and **application-level enforcement** of identity and allowlists.

## Goals / Non-Goals

**Goals:**

- Standard pattern: **WAF → ALB (HTTPS) → OIDC (corporate IdP) → ECS Fargate** running the existing container image; **Bedrock** for LLM using **IAM** (no OpenAI API key required in production if desired).
- **Multi-account**: ECS **task role** may **AssumeRole** into **per-account FinOps reader roles**; mapping is **configuration-driven** (`FINOPS_*` + YAML).
- **Subset of employees**: **IdP enterprise app assignment** (primary) plus optional **group claim allowlist** enforced in the app (secondary).
- **Observability for compliance**: **ALB access logs**, **WAF logs**, and **application audit lines** tied to authenticated identity.
- **Preserve** local development: **Docker + mounted `~/.aws`**, CLI, and current API behavior when **trusted-proxy auth is off**.

**Non-Goals:**

- Choosing a single cloud beyond **AWS** for this change.
- **Cognito** as IdP broker (OIDC direct to corporate IdP is the default; Cognito only if a follow-up change requires it).
- **PrivateLink / VPN** as mandatory (may be documented as future hardening).
- **Per-user AWS credentials** in the browser (users never receive AWS keys).

## Decisions

| Decision | Rationale | Alternatives considered |
|----------|-----------|---------------------------|
| **ECS Fargate** for the app | Long-lived process, **MCP/agent warm-up**, **streaming**; simpler ops than EC2. | Lambda (poor fit for warm-up + streaming without major refactor); raw EC2 (more patching). |
| **ALB OIDC** to corporate IdP | **Standard**, fewer moving parts than Cognito for OIDC-first IdPs; ALB injects identity for the app. | Cognito User Pool federation (reserve for SAML-only mandates). |
| **WAF on ALB** | Required by stakeholders; rate limiting and managed rule sets reduce abuse. | Security Group only (insufficient for L7). |
| **Sticky sessions** on target group | **SSE** and long-lived connections behave predictably with multiple tasks. | Single task (simplest v1); or shared backplane (unnecessary complexity for v1). |
| **Bedrock only in prod** | Keeps LLM traffic **IAM-based** and inside AWS; aligns with internal governance. | OpenAI via Secrets Manager (acceptable for dev; not default for described prod). |
| **AssumeRole per account** | Matches **multi-account** FinOps; task role is **hub**, member accounts **trust** it. | One super-reader in org (often blocked by SCPs / least privilege). |
| **Feature flags via `FINOPS_*` + YAML** | Consistent with project rules; safe defaults for local. | Only env vars (harder to document in template). |

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| **Misconfigured OIDC** exposes the app | Infrastructure review checklist; **deny-by-default** in app when trusted-proxy mode is on; WAF rate limits. |
| **Trust of `X-Forwarded-*` / identity headers** | Only honor identity headers from **trusted proxy mode** intended for ALB; document that **direct access to tasks** must be blocked by SGs; optional signature validation patterns in a follow-up if needed. |
| **Large IdP group claims** | Prefer **one FinOps security group** in the token; avoid sending “all groups” if Entra overage is an issue. |
| **Bedrock model availability** | Pin **model IDs** per region; document fallback/disable behavior for chat if Bedrock is unreachable. |
| **IaC drift** | Keep **docs + IaC** in sync in the same change; version inputs (variables file). |

## Migration Plan

1. **Land application changes** behind **defaults off** (`FINOPS_TRUSTED_PROXY_AUTH` unset/false): no behavior change for existing users.
2. **Add IaC + docs**; deploy to a **non-production** AWS account; register **OIDC** app with **redirect URI** matching ALB listener.
3. **Configure** cross-account **trust** on FinOps reader roles; validate **Cost Explorer** and **Bedrock** from the task role.
4. **Enable** trusted-proxy auth and group allowlist in **staging**; run **smoke tests** (profiles/targets, dashboard, **SSE chat**).
5. **Production cutover**: tighten **IdP assignment**, enable **WAF logging** + **ALB access logs**, set **retention**.

**Rollback:** Disable trusted-proxy auth via config (emergency); scale service to zero; or revert listener rule to **deny all** if catastrophic (break-glass).

## Open Questions

- Exact **header names** ALB forwards for OIDC claims in your AWS partition/account (confirm against AWS docs for your ALB version; map in one module).
- Whether **hostname-only** internal DNS is required before public go-live (org policy).
- **IaC tool** preference: **Terraform** vs **AWS CDK** (tasks leave this as an explicit decision during implementation).
