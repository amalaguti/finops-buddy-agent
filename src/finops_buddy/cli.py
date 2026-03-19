"""CLI entrypoint for FinOps Agent."""

from __future__ import annotations

import argparse
import sys

from dotenv import load_dotenv

from finops_buddy import __version__
from finops_buddy.agent.runner import run_chat_loop
from finops_buddy.context import get_account_context
from finops_buddy.costs import CostExplorerError, get_costs_by_service
from finops_buddy.identity import (
    WrongAccountError,
    get_current_identity,
    get_session,
    list_profiles,
    verify_credentials,
)
from finops_buddy.table import format_costs_table


def cmd_whoami(profile: str | None) -> int:
    """Print current AWS identity (account ID, principal ARN)."""
    try:
        session = get_session(profile_name=profile)
        identity = get_current_identity(session)
        print(f"Account: {identity.account_id}")
        print(f"ARN:     {identity.arn}")
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_profiles(profile: str | None) -> int:
    """List configured AWS profiles from ~/.aws/config."""
    profiles = list_profiles()
    current = profile or __current_profile_from_env()
    for p in profiles:
        marker = " (current)" if p == current else ""
        print(f"  {p}{marker}")
    if not profiles:
        print("  (no named profiles in config)")
    return 0


def __current_profile_from_env() -> str | None:
    return __import__("os").environ.get("AWS_PROFILE")


def cmd_context(profile: str | None) -> int:
    """Print current account and Master/Payer status."""
    try:
        ctx = get_account_context(profile_name=profile)
        print(f"Account: {ctx.account_id}")
        print(f"ARN:    {ctx.arn}")
        print(f"Role:   {ctx.role}")
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_costs(profile: str | None) -> int:
    """Fetch current-month costs by service and print table."""
    try:
        session = get_session(profile_name=profile)
        rows = get_costs_by_service(session)
        print(format_costs_table(rows))
        return 0
    except CostExplorerError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_chat(profile: str | None, *, quiet: bool = False) -> int:
    """Run the interactive Strands chat loop for cost analysis."""
    progress = (lambda m: None) if quiet else None
    return run_chat_loop(profile_name=profile, progress=progress)


def cmd_serve(args: argparse.Namespace) -> int:
    """Start the HTTP API server (uvicorn)."""
    import uvicorn

    from finops_buddy.settings import get_server_host, get_server_port

    host = get_server_host()
    port = get_server_port()
    reload = getattr(args, "reload", False)
    uvicorn.run(
        "finops_buddy.api:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    """Verify AWS credentials for the given profile (or default); optionally require account ID."""
    try:
        identity = verify_credentials(
            profile_name=args.profile,
            expected_account_id=getattr(args, "account_id", None),
        )
        print(f"OK: credentials valid for account {identity.account_id}")
        print(f"  ARN: {identity.arn}")
        return 0
    except WrongAccountError as e:
        print(f"Error: wrong account — expected {e.expected}, got {e.actual}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


class QuotedString(str):
    """String that will be quoted in YAML output."""

    pass


def _quoted_str_representer(dumper, data):
    """YAML representer that forces single quotes for QuotedString."""
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="'")


def cmd_demo_config(args: argparse.Namespace) -> int:
    """Generate config/demo.yaml from AWS profiles for demo mode."""
    import random
    from configparser import ConfigParser
    from pathlib import Path

    import yaml

    yaml.add_representer(QuotedString, _quoted_str_representer)

    city_names = [
        "tokyo",
        "osaka",
        "kyoto",
        "london",
        "paris",
        "berlin",
        "rome",
        "madrid",
        "amsterdam",
        "vienna",
        "prague",
        "dublin",
        "lisbon",
        "stockholm",
        "oslo",
        "helsinki",
        "copenhagen",
        "zurich",
        "geneva",
        "brussels",
        "munich",
        "milan",
        "barcelona",
        "florence",
        "venice",
        "singapore",
        "seoul",
        "sydney",
        "melbourne",
        "toronto",
        "vancouver",
        "montreal",
        "seattle",
        "portland",
        "denver",
        "austin",
        "chicago",
        "boston",
        "miami",
        "atlanta",
        "phoenix",
        "dallas",
        "houston",
    ]
    suffixes = ["prd", "nop", "stg"]

    aws_config_path = Path.home() / ".aws" / "config"
    if not aws_config_path.exists():
        print(f"Error: AWS config not found at {aws_config_path}", file=sys.stderr)
        return 1

    config = ConfigParser()
    config.read(aws_config_path)

    profiles: list[str] = []
    account_ids: dict[str, str] = {}

    for section in config.sections():
        if section.startswith("profile "):
            profile_name = section[8:]
        elif section == "default":
            profile_name = "default"
        else:
            continue
        profiles.append(profile_name)
        sso_account = config.get(section, "sso_account_id", fallback=None)
        role_arn = config.get(section, "role_arn", fallback=None)
        if sso_account:
            account_ids[profile_name] = sso_account
        elif role_arn and "::" in role_arn:
            parts = role_arn.split(":")
            if len(parts) >= 5:
                account_ids[profile_name] = parts[4]

    if not profiles:
        print("No profiles found in AWS config.", file=sys.stderr)
        return 1

    random.shuffle(city_names)
    account_mapping: dict[str, str] = {}
    account_id_mapping: dict[QuotedString, QuotedString] = {}
    seen_account_ids: set[str] = set()

    for i, profile in enumerate(profiles):
        city = city_names[i % len(city_names)]
        suffix = suffixes[i % len(suffixes)]
        fake_name = f"aws-{city}-{suffix}"
        account_mapping[profile] = fake_name

        real_id = account_ids.get(profile)
        if real_id and real_id not in seen_account_ids:
            seen_account_ids.add(real_id)
            fake_id = f"{random.randint(100000000000, 999999999999)}"  # nosec B311
            account_id_mapping[QuotedString(real_id)] = QuotedString(fake_id)

    demo_config = {
        "account_mapping": account_mapping,
        "account_id_mapping": account_id_mapping,
    }

    output_path = Path(__file__).resolve().parents[2] / "config" / "demo.yaml"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# Auto-generated demo config. Do not commit this file.\n")
        f.write("# Regenerate with: finops demo-config\n\n")
        yaml.dump(demo_config, f, default_flow_style=False, sort_keys=False)

    print(f"Generated {output_path}")
    print(f"  {len(account_mapping)} profile mappings")
    print(f"  {len(account_id_mapping)} account ID mappings")
    return 0


def main() -> int:
    """Main CLI entrypoint."""
    load_dotenv()
    load_dotenv(".env.local", override=True)
    parser = argparse.ArgumentParser(
        prog="finops", description="FinOps Agent — AWS cost visibility CLI"
    )
    parser.add_argument(
        "--version",
        "-V",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Show version and exit",
    )
    parser.add_argument(
        "--profile",
        "-p",
        default=None,
        help="AWS profile name (default: AWS_PROFILE or default)",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    whoami_p = subparsers.add_parser("whoami", help="Show current AWS identity")
    whoami_p.set_defaults(func=cmd_whoami)

    profiles_p = subparsers.add_parser("profiles", help="List configured AWS profiles")
    profiles_p.set_defaults(func=cmd_profiles)

    context_p = subparsers.add_parser("context", help="Show account and Master/Payer status")
    context_p.set_defaults(func=cmd_context)

    costs_p = subparsers.add_parser("costs", help="Show current-month costs by service (table)")
    costs_p.add_argument(
        "--profile",
        "-p",
        default=None,
        help="AWS profile name (default: AWS_PROFILE or default)",
    )
    costs_p.set_defaults(func=cmd_costs)

    verify_p = subparsers.add_parser(
        "verify",
        help="Verify AWS credentials for the given profile (or default); optionally --account-id",
    )
    verify_p.add_argument(
        "--profile",
        "-p",
        default=None,
        help="AWS profile name (default: AWS_PROFILE or default)",
    )
    verify_p.add_argument(
        "--account-id",
        "-a",
        default=None,
        metavar="ID",
        help="Require credentials to resolve to this account ID (fail otherwise)",
    )
    verify_p.set_defaults(func=cmd_verify)

    chat_p = subparsers.add_parser(
        "chat",
        help="Start interactive chat with the FinOps agent (cost analysis)",
    )
    chat_p.add_argument(
        "--profile",
        "-p",
        dest="chat_profile",
        default=None,
        help="AWS profile name (default: AWS_PROFILE or default)",
    )
    chat_p.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress startup progress messages",
    )
    chat_p.set_defaults(func=cmd_chat)

    serve_p = subparsers.add_parser(
        "serve",
        help="Start the HTTP API server (profiles, context, costs, chat)",
    )
    serve_p.add_argument(
        "--reload",
        action="store_true",
        help="Reload server when code changes (development)",
    )
    serve_p.set_defaults(func=cmd_serve)

    demo_config_p = subparsers.add_parser(
        "demo-config",
        help="Generate config/demo.yaml from AWS profiles (for demo mode)",
    )
    demo_config_p.set_defaults(func=cmd_demo_config)

    args = parser.parse_args()
    func = getattr(args, "func", None)
    if func is None:
        parser.print_help()
        return 1
    if args.command == "verify":
        return cmd_verify(args)
    if args.command == "chat":
        profile = getattr(args, "chat_profile", None) or args.profile
        return cmd_chat(profile, quiet=getattr(args, "quiet", False))
    if args.command == "serve":
        return cmd_serve(args)
    return func(args.profile)


if __name__ == "__main__":
    sys.exit(main())
