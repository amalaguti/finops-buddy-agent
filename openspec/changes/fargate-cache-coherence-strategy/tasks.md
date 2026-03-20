## 1. Branch

- [ ] 1.1 **non-`main`** branch.

## 2. Documentation first

- [ ] 2.1 Update `docs/DEPLOY_AWS_ARCHITECTURE.md` (or successor) with explicit **per-task vs shared** cache decision and diagrams if needed.
- [ ] 2.2 List metrics to export (warm-up duration, cache hits) as recommendations.

## 3. Implementation (optional phase)

- [ ] 3.1 If Redis chosen: add cache abstraction + `FINOPS_*` config; wire one pilot domain (e.g. mapping cache).
- [ ] 3.2 IaC snippet or README pointers for ElastiCache security groups.

## 4. Quality

- [ ] 4.1 Ruff, Bandit, pytest (including “no Redis when disabled”), pip-audit.
- [ ] 4.2 **`docs/CONFIGURATION.md`** + `config/settings.yaml` for any new settings.

## 5. Spec sync

- [ ] 5.1 Sync deltas to `openspec/specs/` when implementation complete.
