## Why

FinOps Buddy today assumes **local AWS profiles** and a **single-user HTTP backend** suitable for laptops or Docker with mounted `~/.aws`. To run in **AWS for internal FinOps users**, we need a **documented, standard deployment** (ECS Fargate, public HTTPS edge, WAF, OIDC with the corporate IdP), **session-friendly logging**, and **application/runtime changes** so AWS access uses **IAM task roles and STS AssumeRole** into member accounts instead of shared config files—without breaking local CLI and Docker workflows.

## What Changes

- Add a **reference AWS architecture** and **implementation guidance** (IaC scaffold and/or docs): VPC-facing **ECS Fargate**, **ECR**, **internet-facing ALB** with **OIDC** to the corporate IdP, **WAF**, **ALB and WAF logging**, **sticky sessions** (or equivalent) for **SSE/WebSocket** stability when scaled out.
- Extend **AWS identity resolution** with a **cloud deployment mode**: base credentials from the **default boto3 chain** (including **ECS task role**), optional **configured mapping** of logical targets (e.g. account ids / labels) to **role ARNs** for **AssumeRole**, replacing reliance on `~/.aws` for listing and selection in that mode.
- Extend the **HTTP API** with optional **trusted reverse-proxy authentication**: when enabled, requests **without** validated identity context (e.g. ALB OIDC-injected headers) are rejected; optional **IdP group allowlist** for a subset of employees; structured **audit logging** of the authenticated subject (without logging secrets).
- Extend **app settings** with **FINOPS_-prefixed** environment variables and YAML keys for deployment mode, account/role mapping, trusted-proxy auth, group allowlist, and **Bedrock-first** LLM configuration for the deployed environment.
- Update **`docs/CONFIGURATION.md`**, root **README.md** (pointer if needed), and **`config/settings.yaml`** template for all new settings and env vars.
- **BREAKING** for deployments that relied on anonymous network access to the API: in cloud mode with trusted-proxy auth enabled, unauthenticated requests **must** fail (intended; local defaults unchanged).

## Capabilities

### New Capabilities

- `aws-edge-platform`: Reference AWS edge and compute pattern for FinOps Buddy (WAF, ALB HTTPS + OIDC, ECS Fargate, ECR, logging, Bedrock via IAM, documentation and IaC scaffold expectations).

### Modified Capabilities

- `aws-identity`: Add requirements for **cloud runtime** identity (task role + optional AssumeRole map) alongside existing **local profile** behavior.
- `backend-api`: Add requirements for **trusted proxy OIDC** integration, optional **group allowlist**, and **audit logging** when deployment auth is enabled; preserve existing local single-user behavior when disabled.
- `app-settings`: Add requirements for resolving new **deployment** and **cloud identity** settings from YAML and `FINOPS_*` environment variables.

## Impact

- **Code**: `finops_buddy` config, identity/session helpers, FastAPI dependencies/middleware, possibly profile listing endpoints (logical “targets” vs profile names in cloud mode).
- **Docs**: README, new deployment doc, settings template.
- **Infra**: New `infra/` or similar (Terraform/CDK/CDKTF—exact tool chosen during implementation).
- **Dependencies**: None mandatory in Python unless IaC tooling is embedded (prefer separate IaC in repo).
- **Operations**: IdP app registration (OIDC client), ACM certificate, IAM trust policies for cross-account roles, Bedrock model access for the task role.
