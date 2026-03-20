## 1. Branch

- [ ] 1.1 **non-`main`** branch.

## 2. Documentation and IaC

- [ ] 2.1 Add CDN reference section to `docs/DEPLOY_AWS_ARCHITECTURE.md` (or dedicated doc) with diagram (optional).
- [ ] 2.2 Optional: extend `infra/` scaffold with CloudFront + S3 + origin path routing example.

## 3. Application

- [ ] 3.1 Implement `FINOPS_API_ONLY` (or documented name): skip StaticFiles / SPA routes when set.
- [ ] 3.2 Verify health endpoints work for ALB target groups without SPA.
- [ ] 3.3 Frontend: confirm `VITE_API_BASE` documented for split deploy; adjust CORS in FastAPI if needed.

## 4. CI

- [ ] 4.1 Optional: GitHub Action or script to `npm run build` and sync `dist/` to S3.

## 5. Quality

- [ ] 5.1 If Python touched: Ruff, Bandit, pytest, pip-audit.
- [ ] 5.2 If frontend touched: `npm run build` / lint per repo standards.

## 6. Spec sync

- [ ] 6.1 Sync to `openspec/specs/` when implementation complete.
