## 1. Dependencies

- [x] 1.1 Add `bandit>=1.7` to dev dependencies in `pyproject.toml`
- [x] 1.2 Add `pip-audit>=2.7` to dev dependencies in `pyproject.toml`
- [x] 1.3 Run `poetry lock` and `poetry install` to install new dependencies

## 2. Tool Configuration

- [x] 2.1 Add `[tool.bandit]` configuration section to `pyproject.toml` (target `src/`, exclude tests, severity medium+)

## 3. Pre-commit Integration

- [x] 3.1 Add Bandit hook to `.pre-commit-config.yaml`

## 4. Cursor Rules

- [x] 4.1 Create `.cursor/rules/openspec-bandit.mdc` rule for running Bandit during `/opsx-apply` (after Ruff, before pytest)
- [x] 4.2 Create `.cursor/rules/openspec-pip-audit.mdc` rule for running pip-audit once after all tasks complete

## 5. Verification

- [x] 5.1 Run `poetry run ruff check .` and `poetry run ruff format .`; fix any issues
- [x] 5.2 Run `poetry run bandit -c pyproject.toml -r src/` and verify it works; fix any findings
- [x] 5.3 Run `poetry run pip-audit` and verify it works; address any vulnerabilities

## 6. Documentation

- [x] 6.1 Update README.md with a "Development Tools" or "Security Scanning" section documenting Bandit and pip-audit usage
