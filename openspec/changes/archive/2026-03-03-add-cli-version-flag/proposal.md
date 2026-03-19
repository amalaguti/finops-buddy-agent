# Proposal: Add CLI version flag

## Why

Users and scripts need a standard way to check which version of the FinOps Agent CLI is installed (e.g. `finops --version` or `finops -V`). This is a common CLI convention and helps with support and debugging.

## What Changes

- Add a top-level `--version` / `-V` flag to the `finops` CLI.
- When invoked, the CLI prints the package version (e.g. `finops 0.1.0`) and exits with code 0. No subcommand required.
- Reuse the existing `__version__` from `finops_agent.__init__` as the single source of truth.

## Capabilities

### New Capabilities

- `cli-version-flag`: The CLI SHALL support `--version` and `-V` and SHALL print the package version to stdout and exit successfully.

### Modified Capabilities

- None.

## Impact

- **Code:** `src/finops_agent/cli.py` — add version argument to the top-level parser and import `__version__` from the package.
- **Dependencies:** None.
- **Behavior:** Purely additive; no breaking changes.
