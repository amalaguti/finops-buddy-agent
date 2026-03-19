## Why

The codebase handles AWS credentials and cost data but lacks automated security scanning. Adding security tooling to the development workflow catches vulnerabilities early - hardcoded secrets, insecure code patterns, and known CVEs in dependencies - before they reach production.

## What Changes

- Add **Bandit** as a dev dependency for Python security linting (detects hardcoded passwords, SQL injection, insecure functions, etc.)
- Add **pip-audit** as a dev dependency for dependency vulnerability scanning (checks installed packages against known CVEs)
- Create Cursor rules to enforce running both tools during `/opsx-apply` implementation workflow
- Update pre-commit configuration to include Bandit
- Add tool configurations to `pyproject.toml`

## Capabilities

### New Capabilities

(none - this extends existing repo-tooling)

### Modified Capabilities

- `repo-tooling`: Adding requirements for security linting (Bandit) and dependency vulnerability scanning (pip-audit) as part of the development workflow

## Impact

- **Dependencies**: New dev dependencies `bandit>=1.7` and `pip-audit>=2.7`
- **pyproject.toml**: New `[tool.bandit]` configuration section
- **.pre-commit-config.yaml**: New bandit hook
- **.cursor/rules/**: New rule files for OpenSpec apply workflow integration
- **Developer workflow**: Security checks run during `/opsx-apply` and on commit
