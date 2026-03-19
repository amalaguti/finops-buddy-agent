## 1. Branch and setup

- [x] 1.1 Ensure you are not on `main`. Create or switch to a feature branch (e.g. `feature/costs-accept-profile-flag`) before implementing.

## 2. CLI implementation

- [x] 2.1 In `src/finops_agent/cli.py`, add `--profile` / `-p` to the `costs` subparser (same definition as on the root parser and on `verify_p`), so that `finops costs --profile NAME` is accepted and `args.profile` is set for dispatch.

## 3. Lint and format

- [x] 3.1 Run `poetry run ruff check .` and `poetry run ruff format .`; fix any issues.

## 4. Tests

- [x] 4.1 In `tests/test_cli.py`, add or extend pytest tests for the costs subcommand and `--profile`: one test that `finops costs --profile payer-profile` (or equivalent argv) is accepted and passes profile to the handler; one test that `finops --profile X costs` is accepted; one test that `finops costs` without `--profile` uses default (e.g. None). Name tests after the spec scenarios (e.g. `test_costs_profile_after_subcommand`, `test_costs_profile_before_subcommand`, `test_costs_no_profile_uses_default`).
