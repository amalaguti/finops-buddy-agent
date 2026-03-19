# Proposal: Verify AWS credentials for account/profile

## Why

Users need a way to confirm that AWS credentials are valid for a given profile (or default) before running cost or identity commands. This is useful after configuring CLI profiles (including SSO, e.g. `aws sso login --sso-session MySSO_Nave`) or when using environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, optionally `AWS_SESSION_TOKEN`). A dedicated verify flow gives a single, testable entry point and clear success/error messages.

## What Changes

- Add a library helper `verify_credentials(profile_name=None, expected_account_id=None)` in `identity.py` that builds a session, calls STS GetCallerIdentity, and optionally raises `WrongAccountError` when the resolved account ID does not match.
- Add a CLI command `finops verify [--profile NAME] [--account-id ID]` that calls the helper and prints OK (with account ID and ARN) or a clear error (missing/invalid credentials vs wrong account).
- Reuse existing `get_session()` and `get_current_identity()`; no new credential mechanism. Verification works for named profiles (including SSO), env vars, and default profile.

## Capabilities

### New Capabilities

- `verify-credentials`: The system SHALL provide a way to verify that AWS credentials are valid for a given profile (or default chain) and optionally that they resolve to a specific account ID.

### Modified Capabilities

- None.

## Impact

- **Code:** `src/finops_agent/identity.py` (helper, `WrongAccountError`), `src/finops_agent/cli.py` (verify subcommand, including `--profile` on the verify subparser so `finops verify --profile X` works).
- **Docs:** README CLI section documents `finops verify`.
- **Tests:** New tests in `tests/test_identity.py` and `tests/test_cli.py` for verify_credentials and cmd_verify.
- **Behavior:** Purely additive; no breaking changes.
