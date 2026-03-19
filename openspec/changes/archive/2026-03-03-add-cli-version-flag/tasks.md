# Tasks: Add CLI version flag

## 1. Implement version flag

- [x] 1.1 In `cli.py`, import `__version__` from `finops_agent`
- [x] 1.2 Add top-level argument `--version` / `-V` with `action="version"` and `version` set to include `%(prog)s` and `__version__`

## 2. Verify

- [x] 2.1 Run `finops --version` and `finops -V` and confirm output and exit code 0
