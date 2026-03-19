## ADDED Requirements

### Requirement: Bandit security linting

The project SHALL use Bandit as a Python security linter to detect common security issues (hardcoded passwords, SQL injection, insecure function usage, etc.). Bandit SHALL be configured in `pyproject.toml` under `[tool.bandit]`. The configuration SHALL target the `src/` directory and exclude test files. Findings of medium severity or higher SHALL be addressed before implementation is considered complete.

#### Scenario: Bandit runs on source code

- **WHEN** a developer runs `poetry run bandit -c pyproject.toml -r src/`
- **THEN** Bandit scans all Python files in `src/` and reports security findings

#### Scenario: Bandit skips test files

- **WHEN** Bandit runs with the project configuration
- **THEN** files in `tests/` are not scanned (test code may contain intentional patterns)

#### Scenario: Bandit blocks on medium+ severity

- **WHEN** Bandit finds an issue with medium or high severity
- **THEN** the finding SHALL be fixed OR explicitly marked with `# nosec` comment with justification

### Requirement: pip-audit dependency scanning

The project SHALL use pip-audit to scan installed dependencies for known vulnerabilities (CVEs). Developers SHALL run pip-audit before considering implementation complete. Known vulnerabilities with no available fix MAY be ignored with `--ignore-vuln` and documented.

#### Scenario: pip-audit scans dependencies

- **WHEN** a developer runs `poetry run pip-audit`
- **THEN** pip-audit checks all installed packages against known vulnerability databases and reports findings

#### Scenario: pip-audit finds vulnerability with fix available

- **WHEN** pip-audit reports a vulnerability with a fixed version available
- **THEN** the dependency SHALL be updated to the fixed version

#### Scenario: pip-audit finds vulnerability with no fix

- **WHEN** pip-audit reports a vulnerability with no fix available
- **THEN** the finding MAY be ignored with `--ignore-vuln` and the vulnerability SHALL be documented

### Requirement: Bandit in pre-commit hooks

The pre-commit configuration SHALL include a Bandit hook that runs on staged Python files. This ensures security issues are caught at commit time.

#### Scenario: Commit triggers Bandit

- **WHEN** a developer attempts to commit Python files
- **THEN** Bandit runs on staged files and the commit MAY be blocked if security issues are found

### Requirement: OpenSpec apply runs security tools

The `/opsx-apply` workflow SHALL run security tools as part of implementation. Bandit SHALL run after Ruff and before pytest. pip-audit SHALL run once after all tasks are complete. Cursor rules SHALL enforce this execution order.

#### Scenario: Security tools run during apply

- **WHEN** implementing tasks via `/opsx-apply`
- **THEN** Bandit runs after Ruff lint/format, before pytest
- **AND** pip-audit runs once after all tasks complete

#### Scenario: Bandit failure blocks task completion

- **WHEN** Bandit reports medium+ severity issues during `/opsx-apply`
- **THEN** the task is not marked complete until issues are fixed or marked `# nosec`
