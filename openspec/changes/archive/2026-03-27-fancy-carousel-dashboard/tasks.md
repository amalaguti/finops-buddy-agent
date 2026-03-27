## 1. Branch and setup

- [x] 1.1 Create or switch to a feature branch (e.g. `feature/fancy-carousel-dashboard`). Do not implement this change on `main`.

## 2. Carousel UI

- [x] 2.1 Add carousel mode toggle, interval dropdown (10 / 15 / 30 seconds, default 15), and pause/resume for auto-advance in the costs dashboard area (`DashboardSection` or extracted component per `design.md`).
- [x] 2.2 Implement carousel layout with 3D-style CSS (perspective/transforms) and one active slide at a time; map slides to each primary `MiniTable` plus the Savings Plans summary card in the order defined in the delta spec.
- [x] 2.3 When carousel mode is on, force-expand “By cost categories” and “Savings Plans purchase recommendations” so all nested `MiniTable`s participate in the slide list; restore normal collapse behavior when carousel is off.
- [x] 2.4 Honor `prefers-reduced-motion: reduce` (no timer-based auto-advance; minimal or no animated transitions as appropriate).
- [x] 2.5 Keep drill-down/detail overlays out of the carousel slide sequence (per spec).

## 3. Build and quality

- [x] 3.1 Run `cd frontend && npm test` (or the project’s frontend test script) and fix failures.
- [x] 3.2 Run `cd frontend && npm run build:hosted` so `src/finops_buddy/webui/` includes the updated UI.

## 4. Python tooling and tests (repo-wide)

- [x] 4.1 Run `poetry run ruff check .` and `poetry run ruff format .`; fix any issues.
- [x] 4.2 Run `poetry run bandit -c pyproject.toml -r src/`; fix any medium+ findings.
- [x] 4.3 Run `poetry run pytest` and ensure the suite passes (no new Python modules expected; fix any regressions).
- [x] 4.4 Run `poetry run pip-audit`; address or document vulnerabilities per project policy.

## 5. Frontend tests (spec coverage)

- [x] 5.1 Add or extend Vitest tests (see `frontend/src/components/*.test.jsx`) for carousel behavior: e.g. reduced-motion disables auto-advance, interval control updates timing (use fake timers where appropriate), pause stops rotation. Map tests to `specs/costs-dashboard-carousel/spec.md` scenarios where practical.

## 6. OpenSpec completion

- [x] 6.1 After implementation, sync delta spec `openspec/changes/fancy-carousel-dashboard/specs/costs-dashboard-carousel/spec.md` into `openspec/specs/costs-dashboard-carousel/spec.md` if not already merged.
