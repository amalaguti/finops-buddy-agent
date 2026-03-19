"""Account context: current account and Master/Payer status."""

from __future__ import annotations

from dataclasses import dataclass

from finops_buddy.config import get_master_account_id
from finops_buddy.identity import get_current_identity, get_session


@dataclass
class AccountContext:
    """Current account and whether it is considered Master/Payer or linked."""

    account_id: str
    arn: str
    role: str  # "master/payer" | "linked" | "unknown"


def get_account_context(profile_name: str | None = None) -> AccountContext:
    """
    Report current account ID and Master/Payer status.

    Master/Payer account ID comes from FINOPS_MASTER_ACCOUNT_ID if set, else is derived from
    FINOPS_MASTER_PROFILE (STS GetCallerIdentity). If that ID matches current account, role is
    "master/payer"; if set and does not match, "linked"; otherwise "unknown".
    """
    session = get_session(profile_name=profile_name)
    identity = get_current_identity(session)
    master_id = get_master_account_id()
    if master_id is None:
        role = "unknown"
    elif identity.account_id == master_id:
        role = "master/payer"
    else:
        role = "linked"
    return AccountContext(
        account_id=identity.account_id,
        arn=identity.arn,
        role=role,
    )
