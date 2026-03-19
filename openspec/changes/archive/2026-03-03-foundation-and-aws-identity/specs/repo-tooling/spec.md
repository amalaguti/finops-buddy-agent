# Spec: Repo Tooling

## ADDED Requirements

### Requirement: Poetry for build and packaging

The project SHALL use [Poetry](https://python-poetry.org/) for dependency management, build, and packaging. Project metadata and dependency declarations SHALL live in `pyproject.toml` (Poetry format). A `poetry.lock` file SHALL be committed for reproducible installs. Developers SHALL install the environment with `poetry install` and run the CLI or tests via `poetry run` (e.g. `poetry run finops`, `poetry run pytest`).

#### Scenario: Install with Poetry

- **WHEN** a developer runs `poetry install` in the repo root
- **THEN** dependencies are installed from the lockfile and the package is available in the Poetry environment

#### Scenario: Run CLI via Poetry

- **WHEN** a developer runs `poetry run finops whoami` (or `poetry run python -m finops_agent whoami`)
- **THEN** the CLI runs using the Poetry-managed environment

### Requirement: Pre-commit and hooks

The repository SHALL use pre-commit for local hooks. The project SHALL include a `.pre-commit-config.yaml` (or equivalent) that runs at least formatting and linting before commit.

#### Scenario: Developer runs pre-commit install

- **WHEN** a developer runs `pre-commit install` in the repo root
- **THEN** pre-commit hooks are installed for the local repo and run on `git commit`

#### Scenario: Commit triggers lint

- **WHEN** a developer attempts to commit Python files
- **THEN** the configured linter (e.g. Ruff) runs on staged files and the commit MAY be blocked if lint fails

### Requirement: Python linter (Ruff)

The project SHALL use Ruff as the primary Python linter and formatter. Configuration SHALL live in `pyproject.toml` (or a dedicated config file) and SHALL be invoked by pre-commit and optionally CI.

#### Scenario: Ruff runs on codebase

- **WHEN** Ruff is run (e.g. `ruff check .`, `ruff format --check .`)
- **THEN** it reports style and lint issues according to project configuration

### Requirement: Pytest for tests

The project SHALL use pytest for unit (and later integration) tests. Test layout SHALL allow running tests via `pytest` from the repo root; coverage reporting is desired (e.g. `pytest --cov`) with a target of at least 80% for new code (per PROJECT_CONTEXT).

#### Scenario: Developer runs pytest

- **WHEN** a developer runs `pytest` from the repo root
- **THEN** all discovered tests run and results are reported

### Requirement: Project layout for CLI and core

The repository SHALL have a clear Python package layout that supports the CLI entrypoint and future shared core (e.g. a package directory and a way to run the CLI via `python -m <package>` or an installed console script). The layout SHALL allow adding backend and agent code later without restructuring.

#### Scenario: Package is importable

- **WHEN** the project is installed in development mode (e.g. `pip install -e .`) or the repo root is on PYTHONPATH
- **THEN** the main package (e.g. `finops_agent` or `aws_finops_agent`) is importable
