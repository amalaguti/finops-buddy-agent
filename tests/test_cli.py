"""Tests for CLI commands."""

import sys
from unittest.mock import patch

from finops_buddy.identity import CurrentIdentity, WrongAccountError


def test_cmd_verify_success(capsys):
    """Verify command exits 0 and prints OK when credentials are valid."""
    fake_identity = CurrentIdentity(
        account_id="123456789012",
        arn="arn:aws:iam::123456789012:user/test",
        user_id="AIDAEXAMPLE",
    )
    with patch("finops_buddy.cli.verify_credentials", return_value=fake_identity):
        from finops_buddy.cli import cmd_verify

        args = type("Args", (), {"profile": None, "account_id": None})()
        exit_code = cmd_verify(args)
    assert exit_code == 0
    out, err = capsys.readouterr()
    assert "OK" in out
    assert "123456789012" in out
    assert "arn:aws:iam::123456789012:user/test" in out
    assert err == ""


def test_cmd_verify_wrong_account_exits_1(capsys):
    """Verify command exits 1 and prints error when expected account does not match."""
    with patch(
        "finops_buddy.cli.verify_credentials",
        side_effect=WrongAccountError(expected="111111111111", actual="123456789012"),
    ):
        from finops_buddy.cli import cmd_verify

        args = type("Args", (), {"profile": "x", "account_id": "111111111111"})()
        exit_code = cmd_verify(args)
    assert exit_code == 1
    out, err = capsys.readouterr()
    assert "wrong account" in err or "111111111111" in err
    assert "123456789012" in err


def test_cmd_verify_generic_error_exits_1(capsys):
    """Verify command exits 1 and prints error on generic exception."""
    with patch(
        "finops_buddy.cli.verify_credentials",
        side_effect=Exception("No credentials found"),
    ):
        from finops_buddy.cli import cmd_verify

        args = type("Args", (), {"profile": None, "account_id": None})()
        exit_code = cmd_verify(args)
    assert exit_code == 1
    out, err = capsys.readouterr()
    assert "No credentials found" in err or "Error" in err


# --- costs subcommand and --profile (argument order) ---


def test_costs_profile_after_subcommand(capsys):
    """When user runs finops costs --profile NAME, CLI accepts it and passes profile to handler."""
    with patch("finops_buddy.cli.get_costs_by_service", return_value=[]):
        with patch("finops_buddy.cli.get_session"):
            from finops_buddy.cli import main

            old_argv = sys.argv
            try:
                sys.argv = ["finops", "costs", "--profile", "payer-profile"]
                exit_code = main()
            finally:
                sys.argv = old_argv
    assert exit_code == 0
    out, _ = capsys.readouterr()
    assert "No cost data" in out or "Service" in out  # table or empty message


def test_costs_profile_before_subcommand(capsys):
    """When user runs finops --profile X costs, CLI accepts it and runs costs for that profile."""
    with patch("finops_buddy.cli.get_costs_by_service", return_value=[]):
        with patch("finops_buddy.cli.get_session"):
            from finops_buddy.cli import main

            old_argv = sys.argv
            try:
                sys.argv = ["finops", "--profile", "MyProfile", "costs"]
                exit_code = main()
            finally:
                sys.argv = old_argv
    assert exit_code == 0
    out, _ = capsys.readouterr()
    assert "No cost data" in out or "Service" in out


def test_costs_no_profile_uses_default(capsys):
    """When user runs finops costs without --profile, CLI uses default profile (None)."""
    with patch("finops_buddy.cli.get_costs_by_service", return_value=[]):
        get_session = patch("finops_buddy.cli.get_session")
        with get_session as mock_session:
            from finops_buddy.cli import main

            old_argv = sys.argv
            try:
                sys.argv = ["finops", "costs"]
                exit_code = main()
            finally:
                sys.argv = old_argv
    assert exit_code == 0
    mock_session.assert_called_once_with(profile_name=None)
