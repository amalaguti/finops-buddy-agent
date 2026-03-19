# Tasks: Verify AWS credentials

## 1. Identity module

- [x] 1.1 Add WrongAccountError exception (expected, actual) in identity.py
- [x] 1.2 Add verify_credentials(profile_name=None, expected_account_id=None) that builds session, calls get_current_identity(session), compares account_id when expected_account_id is set, raises WrongAccountError on mismatch, returns CurrentIdentity on success

## 2. CLI

- [x] 2.1 Add verify subparser with help text for verifying credentials
- [x] 2.2 Add --account-id / -a to verify subparser (optional)
- [x] 2.3 Add --profile / -p to verify subparser so `finops verify --profile X` works
- [x] 2.4 Implement cmd_verify(args) that calls verify_credentials(profile_name=args.profile, expected_account_id=args.account_id), prints OK + identity or handles WrongAccountError and generic exceptions with clear stderr messages and exit 1

## 3. Documentation

- [x] 3.1 Update README CLI section with verify command and optional --account-id

## 4. Tests

- [x] 4.1 Add pytest tests for verify_credentials: no expected account (returns identity); expected account matches (returns identity); expected account mismatch (raises WrongAccountError)
- [x] 4.2 Add pytest tests for cmd_verify: success (exit 0, OK and ARN in stdout); wrong account (exit 1, error on stderr); generic error (exit 1, error on stderr)

## 5. Quality

- [x] 5.1 Run `poetry run ruff check .` and `poetry run ruff format .`; fix any issues
- [x] 5.2 Run `poetry run pytest`; all tests pass
