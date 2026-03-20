## 1. Branch and scope

- [ ] 1.1 **Before implementing:** ensure work is on a **non-`main`** branch (e.g. `feature/deploy-aws`); create and switch if currently on `main`.

## 2. Design decisions frozen in code/docs

- [ ] 2.1 Confirm **IaC tool** (Terraform vs CDK) and document the choice in the IaC README referenced by `aws-edge-platform`.
- [ ] 2.2 Document **exact ALB/OIDC identity headers** the FastAPI app will trust (map from AWS documentation for the ALB authenticate action) in `design.md` follow-up or deployment doc.

## 3. Documentation and template (aws-edge-platform, app-settings)

- [ ] 3.1 Add **reference deployment documentation** (`docs/` path as per spec) covering WAF, ALB HTTPS + OIDC, ECS Fargate, ECR, logging, stickiness/SSE, cross-account AssumeRole, Bedrock/IAM.
- [ ] 3.2 Add **IaC scaffold** with README listing inputs (VPC, ACM, OIDC, secrets) and WAF/ALB logging; use placeholders only.
- [ ] 3.3 Update **`docs/CONFIGURATION.md`** (and link from root **README.md** if needed) with all new `FINOPS_*` variables: `FINOPS_CLOUD_DEPLOYMENT_MODE`, `FINOPS_ASSUMABLE_TARGETS_JSON`, `FINOPS_TRUSTED_PROXY_AUTH`, `FINOPS_ALLOWED_IDP_GROUPS`, `FINOPS_LLM_PROVIDER`, and any header/trust notes.
- [ ] 3.4 Update **`config/settings.yaml`** template with new keys (commented or placeholder): `deployment.cloud_mode`, FinOps target map structure, `deployment.trusted_proxy_auth`, `deployment.allowed_idp_groups`, `deployment.llm_provider` (or equivalent names aligned with code).

## 4. Settings resolution (app-settings spec)

- [ ] 4.1 Implement resolution for cloud deployment mode, assumable target map, trusted proxy auth, allowlist, and `FINOPS_LLM_PROVIDER` in the settings module with documented precedence (env overrides YAML where specified).

## 5. AWS identity and sessions (aws-identity spec)

- [ ] 5.1 Implement **cloud deployment mode** session factory using the default boto3 chain when enabled.
- [ ] 5.2 Implement **FinOps target map** parsing and **STS AssumeRole** per selected target; integrate with API/profile selection paths so listing and costs/chat use the assumed session when in cloud mode.

## 6. HTTP API (backend-api spec)

- [ ] 6.1 Add **middleware or dependencies** for **trusted reverse-proxy authentication** when `FINOPS_TRUSTED_PROXY_AUTH` is true: reject missing identity context with 401/403.
- [ ] 6.2 Implement **optional `FINOPS_ALLOWED_IDP_GROUPS`** check against parsed group claims.
- [ ] 6.3 Add **audit logging** (stable user id, no secrets) for allowed requests when trusted proxy auth is enabled.
- [ ] 6.4 Ensure **SSE/WebSocket** chat paths still function behind ALB when gate is enabled (integration smoke or documented manual check).

## 7. Agent / LLM (Bedrock preference)

- [ ] 7.1 Implement **`FINOPS_LLM_PROVIDER=bedrock`** (and YAML equivalent) so Bedrock is selected per app-settings spec when set.

## 8. Quality gates

- [ ] 8.1 Run `poetry run ruff check .` and `poetry run ruff format .`; fix any issues.
- [ ] 8.2 Run `poetry run bandit -c pyproject.toml -r src/`; fix any medium+ findings.
- [ ] 8.3 Add or extend **pytest** tests in `tests/`: one test per new **#### Scenario** where practical (settings resolution, middleware allow/deny, identity map parsing, optional IaC/doc existence if tested via thin helpers).
- [ ] 8.4 Run `poetry run pytest`.
- [ ] 8.5 Run `poetry run pip-audit`; address or document any findings.

## 9. OpenSpec completion

- [ ] 9.1 After all tasks are done, if delta specs exist under `openspec/changes/deploy-aws/specs/`, **sync** them to `openspec/specs/` per project workflow (user confirmation if required) before archiving.
- [ ] 9.2 **Do not** merge implementation work to `main` from this branch until review passes.
