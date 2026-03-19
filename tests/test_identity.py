"""Tests for identity, profile listing, and credential verification."""

import os
import tempfile
from unittest.mock import patch

import pytest

from finops_buddy.identity import (
    CurrentIdentity,
    WrongAccountError,
    get_profile_account_ids_from_local_files,
    list_profiles,
    verify_credentials,
)
from finops_buddy.settings import reset_settings_cache


@pytest.fixture(autouse=True)
def _reset_settings():
    """Reset settings cache and clear env so tests don't inherit shell/.env.local or real config."""
    reset_settings_cache()
    # Clear env so each test starts with a clean slate
    for key in (
        "FINOPS_EXCLUDED_PROFILES",
        "FINOPS_INCLUDED_ONLY_PROFILES",
        "AWS_CONFIG_FILE",
        "AWS_SHARED_CREDENTIALS_FILE",
        "FINOPS_CONFIG_FILE",
    ):
        os.environ.pop(key, None)
    # Force settings to not load from repo/default config (use nonexistent path so YAML returns [])
    os.environ["FINOPS_CONFIG_FILE"] = tempfile.mktemp(suffix=".yaml")
    yield
    reset_settings_cache()
    for key in (
        "FINOPS_EXCLUDED_PROFILES",
        "FINOPS_INCLUDED_ONLY_PROFILES",
        "AWS_CONFIG_FILE",
        "AWS_SHARED_CREDENTIALS_FILE",
        "FINOPS_CONFIG_FILE",
    ):
        os.environ.pop(key, None)


def test_list_profiles_excludes_configured_names(tmp_path, monkeypatch):
    """When app settings define excluded list, only profiles not in it are returned."""
    aws_config = tmp_path / "config"
    aws_config.write_text(
        "[profile a]\nregion = us-east-1\n"
        "[profile b]\nregion = us-east-1\n"
        "[profile c]\nregion = us-east-1\n"
    )
    monkeypatch.setenv("AWS_CONFIG_FILE", str(aws_config))
    monkeypatch.setenv("FINOPS_EXCLUDED_PROFILES", "b")
    assert list_profiles() == ["a", "c"]


def test_list_profiles_returns_all_when_no_exclusions(tmp_path, monkeypatch):
    """When excluded list is empty, all configured profiles are returned."""
    aws_config = tmp_path / "config"
    aws_config.write_text("[profile a]\nregion = us-east-1\n[profile b]\nregion = us-east-1\n")
    monkeypatch.setenv("AWS_CONFIG_FILE", str(aws_config))
    monkeypatch.delenv("FINOPS_EXCLUDED_PROFILES", raising=False)
    monkeypatch.delenv("FINOPS_INCLUDED_ONLY_PROFILES", raising=False)
    assert list_profiles() == ["a", "b"]


def test_list_profiles_only_included_when_allowlist_set(tmp_path, monkeypatch):
    """When included_only_profiles is set, only those in the list are returned."""
    aws_config = tmp_path / "config"
    aws_config.write_text(
        "[profile a]\nregion = us-east-1\n"
        "[profile b]\nregion = us-east-1\n"
        "[profile c]\nregion = us-east-1\n"
    )
    monkeypatch.setenv("AWS_CONFIG_FILE", str(aws_config))
    monkeypatch.setenv("FINOPS_INCLUDED_ONLY_PROFILES", "a,c")
    monkeypatch.delenv("FINOPS_EXCLUDED_PROFILES", raising=False)
    assert list_profiles() == ["a", "c"]


def test_list_profiles_allowlist_takes_precedence_over_blocklist(tmp_path, monkeypatch):
    """When both included_only and excluded are set, allowlist wins."""
    aws_config = tmp_path / "config"
    aws_config.write_text(
        "[profile a]\nregion = us-east-1\n"
        "[profile b]\nregion = us-east-1\n"
        "[profile c]\nregion = us-east-1\n"
    )
    monkeypatch.setenv("AWS_CONFIG_FILE", str(aws_config))
    monkeypatch.setenv("FINOPS_INCLUDED_ONLY_PROFILES", "b")
    monkeypatch.setenv("FINOPS_EXCLUDED_PROFILES", "a")
    assert list_profiles() == ["b"]


def test_list_profiles_empty_allowlist_uses_blocklist(tmp_path, monkeypatch):
    """When included_only is empty, excluded_profiles blocklist is used."""
    aws_config = tmp_path / "config"
    aws_config.write_text("[profile a]\nregion = us-east-1\n[profile b]\nregion = us-east-1\n")
    monkeypatch.setenv("AWS_CONFIG_FILE", str(aws_config))
    monkeypatch.delenv("FINOPS_INCLUDED_ONLY_PROFILES", raising=False)
    monkeypatch.setenv("FINOPS_EXCLUDED_PROFILES", "a")
    assert list_profiles() == ["b"]


def test_get_profile_account_ids_from_local_files_parses_sso_and_role_arn(
    tmp_path,
    monkeypatch,
):
    """Local parser resolves account ids from sso_account_id and role_arn without STS."""
    aws_config = tmp_path / "config"
    aws_config.write_text(
        "[profile sso]\n"
        "sso_account_id = 111122223333\n"
        "region = us-east-1\n"
        "[profile role]\n"
        "role_arn = arn:aws:iam::444455556666:role/Admin\n"
        "source_profile = base\n"
        "[profile noid]\n"
        "region = us-east-1\n"
    )
    monkeypatch.setenv("AWS_CONFIG_FILE", str(aws_config))
    mapping = get_profile_account_ids_from_local_files(["sso", "role", "noid"])
    assert mapping == {
        "sso": "111122223333",
        "role": "444455556666",
    }


def test_get_profile_account_ids_from_local_files_reads_credentials_sections(
    tmp_path,
    monkeypatch,
):
    """Local parser also checks credentials-style section names when needed."""
    aws_config = tmp_path / "config"
    credentials = tmp_path / "credentials"
    aws_config.write_text("[profile app]\nregion = us-east-1\n")
    credentials.write_text("[app]\nrole_arn = arn:aws:iam::777788889999:role/Developer\n")
    monkeypatch.setenv("AWS_CONFIG_FILE", str(aws_config))
    monkeypatch.setenv("AWS_SHARED_CREDENTIALS_FILE", str(credentials))
    mapping = get_profile_account_ids_from_local_files(["app"])
    assert mapping == {"app": "777788889999"}


# --- verify_credentials ---


def test_verify_credentials_returns_identity_when_no_expected_account():
    """When expected_account_id is not set, verify_credentials returns CurrentIdentity."""
    fake_identity = CurrentIdentity(
        account_id="123456789012",
        arn="arn:aws:iam::123456789012:user/test",
        user_id="AIDAEXAMPLE",
    )
    with (
        patch("finops_buddy.identity.get_session") as mock_get_session,
        patch("finops_buddy.identity.get_current_identity", return_value=fake_identity),
    ):
        result = verify_credentials(profile_name="my-profile")
    assert result == fake_identity
    mock_get_session.assert_called_once_with(profile_name="my-profile")


def test_verify_credentials_returns_identity_when_expected_account_matches():
    """When expected_account_id matches resolved account, verify_credentials returns identity."""
    fake_identity = CurrentIdentity(
        account_id="123456789012",
        arn="arn:aws:iam::123456789012:user/test",
        user_id="AIDAEXAMPLE",
    )
    with (
        patch("finops_buddy.identity.get_session"),
        patch("finops_buddy.identity.get_current_identity", return_value=fake_identity),
    ):
        result = verify_credentials(
            profile_name=None,
            expected_account_id="123456789012",
        )
    assert result == fake_identity


def test_verify_credentials_raises_wrong_account_when_mismatch():
    """When expected_account_id does not match resolved account, WrongAccountError is raised."""
    fake_identity = CurrentIdentity(
        account_id="123456789012",
        arn="arn:aws:iam::123456789012:user/test",
        user_id="AIDAEXAMPLE",
    )
    with (
        patch("finops_buddy.identity.get_session"),
        patch("finops_buddy.identity.get_current_identity", return_value=fake_identity),
    ):
        with pytest.raises(WrongAccountError) as exc_info:
            verify_credentials(
                profile_name="other",
                expected_account_id="999999999999",
            )
    assert exc_info.value.expected == "999999999999"
    assert exc_info.value.actual == "123456789012"
    assert "999999999999" in str(exc_info.value)
    assert "123456789012" in str(exc_info.value)
