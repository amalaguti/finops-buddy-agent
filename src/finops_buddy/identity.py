"""AWS identity resolution and profile listing."""

from __future__ import annotations

import configparser
import os
import re
from dataclasses import dataclass
from pathlib import Path

import boto3

from finops_buddy.settings import get_excluded_profiles, get_included_only_profiles


class WrongAccountError(Exception):
    """Raised when credentials resolve to a different account than expected."""

    def __init__(self, expected: str, actual: str) -> None:
        self.expected = expected
        self.actual = actual
        super().__init__(f"Expected account {expected}, got {actual}")


@dataclass
class CurrentIdentity:
    """Current AWS caller identity from STS GetCallerIdentity."""

    account_id: str
    arn: str
    user_id: str


_ACCOUNT_ID_RE = re.compile(r"arn:[^:]+:iam::(\d{12}):")


def get_session(profile_name: str | None = None, region_name: str | None = None):
    """
    Create a boto3 session from default chain or from the given profile.

    Uses AWS_PROFILE env if profile_name is None. Region uses AWS_DEFAULT_REGION
    or the session default if region_name is None.
    """
    session_kw: dict = {}
    if profile_name is not None:
        session_kw["profile_name"] = profile_name
    if region_name is not None:
        session_kw["region_name"] = region_name
    return boto3.Session(**session_kw)


def get_current_identity(session: boto3.Session) -> CurrentIdentity:
    """
    Call STS GetCallerIdentity with the given session and return account ID and principal ARN.

    Raises:
        NoCredentialsError: If no credentials are available.
        ClientError: On STS API errors.
    """
    sts = session.client("sts")
    resp = sts.get_caller_identity()
    return CurrentIdentity(
        account_id=resp["Account"],
        arn=resp["Arn"],
        user_id=resp["UserId"],
    )


def verify_credentials(
    profile_name: str | None = None,
    expected_account_id: str | None = None,
) -> CurrentIdentity:
    """
    Verify AWS credentials for the default chain or given profile.

    Builds a session (profile or default), calls STS GetCallerIdentity. If
    expected_account_id is set, raises WrongAccountError when the resolved
    account does not match.

    Returns:
        CurrentIdentity on success.

    Raises:
        WrongAccountError: When expected_account_id is set and does not match.
        NoCredentialsError: If no credentials are available.
        ClientError: On STS API errors.
    """
    session = get_session(profile_name=profile_name)
    identity = get_current_identity(session)
    if expected_account_id is not None and identity.account_id != expected_account_id:
        raise WrongAccountError(expected=expected_account_id, actual=identity.account_id)
    return identity


def get_config_path() -> Path:
    """Return the AWS config file path (AWS_CONFIG_FILE or ~/.aws/config)."""
    path = os.environ.get("AWS_CONFIG_FILE")
    if path:
        return Path(path)
    return Path.home() / ".aws" / "config"


def get_credentials_path() -> Path:
    """Return the AWS shared credentials path (env override or ~/.aws/credentials)."""
    path = os.environ.get("AWS_SHARED_CREDENTIALS_FILE")
    if path:
        return Path(path)
    return Path.home() / ".aws" / "credentials"


def _read_ini_file(path: Path) -> configparser.RawConfigParser:
    """Read an INI-style AWS config/credentials file if present."""
    parser = configparser.RawConfigParser()
    if path.exists():
        parser.read(path, encoding="utf-8")
    return parser


def _extract_account_id_from_section(
    parser: configparser.RawConfigParser,
    section_name: str,
) -> str | None:
    """Extract account ID from a parsed profile section when present."""
    if not parser.has_section(section_name):
        return None
    sso_account_id = parser.get(section_name, "sso_account_id", fallback="").strip()
    if sso_account_id.isdigit() and len(sso_account_id) == 12:
        return sso_account_id
    role_arn = parser.get(section_name, "role_arn", fallback="").strip()
    if role_arn:
        match = _ACCOUNT_ID_RE.search(role_arn)
        if match:
            return match.group(1)
    return None


def get_profile_account_ids_from_local_files(
    profile_names: list[str] | None = None,
) -> dict[str, str]:
    """
    Resolve profile -> account ID from local AWS config/credentials without STS.

    Supports common SSO and role-based profiles:
    - `sso_account_id`
    - `role_arn` (extract account id from ARN)
    """
    names = profile_names or list_profiles()
    if not names:
        return {}

    config_parser = _read_ini_file(get_config_path())
    credentials_parser = _read_ini_file(get_credentials_path())
    mapping: dict[str, str] = {}
    for name in names:
        for section_name in (f"profile {name}", name):
            account_id = _extract_account_id_from_section(config_parser, section_name)
            if account_id is None:
                account_id = _extract_account_id_from_section(
                    credentials_parser,
                    section_name,
                )
            if account_id:
                mapping[name] = account_id
                break
    return mapping


def list_profiles() -> list[str]:
    """
    Read the shared config file and return profile names.

    When included_only_profiles is non-empty, returns only profiles in that list
    (intersection with config). Otherwise excludes profiles in excluded_profiles list.
    Parses [profile <name>] sections.
    """
    config_path = get_config_path()
    if not config_path.exists():
        return []
    profiles = []
    with open(config_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("[profile ") and line.endswith("]"):
                name = line[9:-1].strip()
                if name:
                    profiles.append(name)
    included = get_included_only_profiles()
    if included:
        included_set = set(included)
        return [p for p in profiles if p in included_set]
    excluded = set(get_excluded_profiles())
    if not excluded:
        return profiles
    return [p for p in profiles if p not in excluded]
