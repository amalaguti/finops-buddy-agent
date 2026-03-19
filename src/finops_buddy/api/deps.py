"""FastAPI dependencies for profile and request context."""

from __future__ import annotations

import os

from fastapi import Header, Query

from finops_buddy.identity import list_profiles


def resolve_profile(
    profile: str | None = Query(None, description="AWS profile name"),
    x_aws_profile: str | None = Header(None, alias="X-AWS-Profile"),
) -> str | None:
    """
    Resolve the AWS profile for this request.

    Uses, in order: query param `profile`, header `X-AWS-Profile`,
    env AWS_PROFILE, or first profile from list_profiles().
    """
    if profile is not None and profile.strip():
        return profile.strip()
    if x_aws_profile is not None and x_aws_profile.strip():
        return x_aws_profile.strip()
    env_profile = os.environ.get("AWS_PROFILE")
    if env_profile is not None and env_profile.strip():
        return env_profile.strip()
    profiles = list_profiles()
    return profiles[0] if profiles else None
