## Context

The project uses Poetry for dependency management, Ruff for linting/formatting, and pytest for testing. Pre-commit hooks enforce Ruff on commit. The OpenSpec `/opsx-apply` workflow has Cursor rules that enforce running Ruff and pytest during implementation.

Currently there is no security scanning. The codebase handles AWS credentials (via boto3 sessions) and cost data, making security scanning valuable.

## Goals / Non-Goals

**Goals:**
- Add Bandit for Python security linting (detect insecure code patterns)
- Add pip-audit for dependency vulnerability scanning (detect CVEs)
- Integrate both tools into the `/opsx-apply` workflow via Cursor rules
- Add Bandit to pre-commit hooks for commit-time checking
- Keep the workflow fast - security checks should not significantly slow down development

**Non-Goals:**
- Container image scanning (trivy) - out of scope for this change
- Type checking (mypy/pyright) - separate concern, separate change
- Custom security rules (semgrep) - can be added later if needed
- CI/CD integration - this change focuses on local development workflow

## Decisions

### Decision 1: Bandit configuration in pyproject.toml

**Choice**: Configure Bandit via `[tool.bandit]` section in `pyproject.toml`

**Rationale**: Keeps all tool configuration in one place. Bandit supports pyproject.toml natively since v1.7.

**Configuration**:
- Target: `src/` directory (skip tests for security scanning)
- Severity: Medium and above (skip low-severity noise)
- Skip tests directory (test code may have intentional "insecure" patterns for testing)

**Alternatives considered**:
- `.bandit` file: Extra file to maintain, less discoverable
- Command-line args only: Not reproducible, easy to forget flags

### Decision 2: pip-audit runs once per change, not per task

**Choice**: Run pip-audit at the end of implementation (after all tasks), not after each task

**Rationale**: pip-audit checks dependencies, which rarely change during a single implementation. Running once at the end is sufficient and faster.

**Alternatives considered**:
- Run per task: Wasteful, dependencies don't change that often
- Run only at archive: Too late to catch issues

### Decision 3: Cursor rule execution order

**Choice**: Run tools in this order during `/opsx-apply`:
1. Ruff lint + format (existing)
2. Bandit security scan (new)
3. Pytest (existing)
4. pip-audit (new, once at end)

**Rationale**: 
- Ruff first: Fast, catches syntax/style issues that would fail other tools
- Bandit before tests: Security issues in new code caught before writing tests for it
- pip-audit last: Only relevant once, checks dependencies not code

### Decision 4: Bandit in pre-commit, pip-audit not

**Choice**: Add Bandit to `.pre-commit-config.yaml`, but not pip-audit

**Rationale**: 
- Bandit: Fast, checks staged files only, valuable per-commit
- pip-audit: Slower, checks all dependencies, overkill for every commit

### Decision 5: Bandit failure blocks implementation

**Choice**: Bandit findings of medium severity or higher SHALL block implementation (must be fixed or explicitly skipped with `# nosec` comment)

**Rationale**: Security issues should not be deferred. The `# nosec` escape hatch exists for false positives.

## Risks / Trade-offs

**[Risk] False positives from Bandit** → Mitigation: Use `# nosec` comments with justification. Configure severity threshold to skip low-severity noise.

**[Risk] pip-audit blocks on unfixable CVE** → Mitigation: Can use `--ignore-vuln` for known issues with no fix available. Document ignored vulnerabilities.

**[Risk] Slower development loop** → Mitigation: Bandit is fast (~1-2 seconds for this codebase). pip-audit runs once per change, not per task.

**[Trade-off] Security vs. speed**: Chose to run Bandit per-task (catches issues early) but pip-audit once (dependencies rarely change). Balance of thoroughness and speed.
