# Design: Verify AWS credentials

## Context

The app already uses `get_session(profile_name=...)` and `get_current_identity(session)` (STS GetCallerIdentity). Verification is "credentials valid and optionally for this account" with no new credential chain or SSO logic.

## Goals / Non-Goals

**Goals:**
- Single library entry point: verify credentials for a profile (or default) and optionally require a specific account ID.
- CLI command that prints clear success or error (wrong account vs missing/invalid credentials).
- Support both `finops verify --profile X` and `finops --profile X verify` (profile on verify subparser so order works).

**Non-Goals:**
- No "account name" / profile-name cross-check (redundant with --profile).
- No presence-only check without STS; validity is determined by STS only.

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Verification method** | STS GetCallerIdentity via existing get_current_identity(session) | Standard, works for profile/SSO/env; no extra APIs. |
| **Wrong account** | Custom WrongAccountError(expected, actual) | Clear exception for optional account-id mismatch; CLI can print a dedicated message. |
| **CLI profile** | Add --profile / -p to verify subparser | Global --profile is only parsed before subcommand; adding to verify subparser allows `finops verify --profile X`. |
| **No account-name flag** | Only --profile and --account-id | "Verify access to profile X" is just `finops verify --profile X`; no second profile-name concept. |

## Risks / Trade-offs

- None; reuses existing session and STS logic.
