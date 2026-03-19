"""Optional config for Master/Payer account and other settings."""

from __future__ import annotations

import os

_MASTER_ACCOUNT_ID_ENV = "FINOPS_MASTER_ACCOUNT_ID"
_MASTER_PROFILE_ENV = "FINOPS_MASTER_PROFILE"

# Sentinel and cache for account ID derived from FINOPS_MASTER_PROFILE (avoids repeated STS calls).
_SENTINEL = object()
_resolved_master_account_id: str | None | object = _SENTINEL


def get_master_profile() -> str | None:
    """
    Return the configured Master/Payer AWS profile name, or None if not set.

    Reads from environment variable FINOPS_MASTER_PROFILE. Preferred single source
    of truth for "which profile is the payer"; master account ID can be derived from it.
    """
    value = os.environ.get(_MASTER_PROFILE_ENV)
    return value.strip() if value else None


def get_master_account_id() -> str | None:
    """
    Return the Master/Payer account ID, or None if not configured.

    Uses FINOPS_MASTER_ACCOUNT_ID when set. Otherwise, when FINOPS_MASTER_PROFILE
    is set, resolves the account ID from that profile (via STS GetCallerIdentity)
    and caches it. So you only need FINOPS_MASTER_PROFILE; FINOPS_MASTER_ACCOUNT_ID
    is optional and can override the derived value.
    """
    explicit = os.environ.get(_MASTER_ACCOUNT_ID_ENV)
    if explicit and explicit.strip():
        return explicit.strip()

    profile = get_master_profile()
    if not profile:
        return None

    global _resolved_master_account_id
    if _resolved_master_account_id is not _SENTINEL:
        return _resolved_master_account_id  # type: ignore[return-value]

    try:
        from finops_buddy.identity import get_current_identity, get_session

        session = get_session(profile_name=profile)
        identity = get_current_identity(session)
        _resolved_master_account_id = identity.account_id
        return _resolved_master_account_id
    except Exception:
        _resolved_master_account_id = None
        return None
