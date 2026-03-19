# Spec: CLI version flag

## ADDED Requirements

### Requirement: Version flag prints package version and exits

The CLI SHALL accept a top-level `--version` and `-V` flag. When either is passed, the CLI SHALL print the package version (e.g. `finops 0.1.0` or equivalent) to stdout and exit with code 0. The version value SHALL come from the package’s single source of truth (e.g. `finops_agent.__version__`). No subcommand SHALL be required when `--version` or `-V` is used.

#### Scenario: User passes --version

- **WHEN** the user runs `finops --version`
- **THEN** the CLI prints the version string to stdout and exits with code 0

#### Scenario: User passes -V

- **WHEN** the user runs `finops -V`
- **THEN** the CLI prints the version string to stdout and exits with code 0

#### Scenario: Version matches package

- **WHEN** the package version is `0.1.0` and the user runs `finops --version`
- **THEN** the output includes `0.1.0`
