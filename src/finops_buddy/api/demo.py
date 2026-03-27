"""Demo mode utilities for masking sensitive AWS identifiers."""

from __future__ import annotations

import re
from typing import Any

DEMO_MASK_ARN_SESSION_NAME = "john.doe@finops.buddy"


def mask_account_name(name: str, mapping: dict[str, str]) -> str:
    """
    Mask an account or profile name using the provided mapping.
    If no mapping exists, generate a fake name like Account_001.
    """
    if not name:
        return name
    if name in mapping:
        return mapping[name]
    return _generate_fake_name(name, mapping)


def _generate_fake_name(name: str, mapping: dict[str, str]) -> str:
    """Generate a consistent fake name for unmapped accounts."""
    existing_generated = [v for v in mapping.values() if v.startswith("Account_")]
    next_num = len(existing_generated) + 1
    fake_name = f"Account_{next_num:03d}"
    mapping[name] = fake_name
    return fake_name


def mask_account_id(account_id: str, mapping: dict[str, str]) -> str:
    """
    Mask a 12-digit AWS account ID using the provided mapping.
    If no mapping exists, generate a fake ID like 000000000001.
    """
    if not account_id:
        return account_id
    if account_id in mapping:
        return mapping[account_id]
    return _generate_fake_id(account_id, mapping)


def _generate_fake_id(account_id: str, mapping: dict[str, str]) -> str:
    """Generate a consistent fake account ID for unmapped IDs."""
    existing_generated = [v for v in mapping.values() if re.match(r"^0{11}\d$", v)]
    next_num = len(existing_generated) + 1
    fake_id = f"{next_num:012d}"
    mapping[account_id] = fake_id
    return fake_id


def mask_response_data(
    data: Any,
    name_mapping: dict[str, str],
    id_mapping: dict[str, str],
) -> Any:
    """
    Recursively mask account names and IDs in API response data.
    Handles dicts, lists, and primitive values.
    """
    if isinstance(data, dict):
        return _mask_dict(data, name_mapping, id_mapping)
    if isinstance(data, list):
        return [mask_response_data(item, name_mapping, id_mapping) for item in data]
    if isinstance(data, str):
        return _mask_string_value(data, name_mapping, id_mapping)
    return data


def _mask_dict(
    data: dict,
    name_mapping: dict[str, str],
    id_mapping: dict[str, str],
) -> dict:
    """Mask sensitive fields in a dictionary."""
    result = {}
    for key, value in data.items():
        if key in ("account_id", "accountId", "Account", "account"):
            if isinstance(value, str) and re.match(r"^\d{12}$", value):
                result[key] = mask_account_id(value, id_mapping)
            else:
                result[key] = mask_response_data(value, name_mapping, id_mapping)
        elif key in (
            "profile",
            "master_profile",
            "profile_name",
            "profileName",
            "name",
            "account_name",
            "accountName",
            "value_key",
        ):
            if isinstance(value, str):
                result[key] = mask_account_name(value, name_mapping)
            else:
                result[key] = mask_response_data(value, name_mapping, id_mapping)
        elif key == "profiles" and isinstance(value, list):
            result[key] = [
                mask_account_name(p, name_mapping) if isinstance(p, str) else p for p in value
            ]
        elif key == "arn" and isinstance(value, str):
            result[key] = _mask_arn_value(value, id_mapping)
        else:
            result[key] = mask_response_data(value, name_mapping, id_mapping)
    return result


def _mask_string_value(
    value: str,
    name_mapping: dict[str, str],
    id_mapping: dict[str, str],
) -> str:
    """Mask account IDs found in string values (e.g., ARNs)."""

    def replace_id(match: re.Match) -> str:
        return mask_account_id(match.group(0), id_mapping)

    return re.sub(r"\b\d{12}\b", replace_id, value)


def _mask_arn_value(arn: str, id_mapping: dict[str, str]) -> str:
    """
    Mask ARN for demo: replace account IDs and assumed-role session name.
    Session name after the last "/" in assumed-role ARNs becomes
    DEMO_MASK_ARN_SESSION_NAME.
    """
    masked = _mask_string_value(arn, {}, id_mapping)
    if "/assumed-role/" in masked or ":assumed-role/" in masked:
        last_slash = masked.rfind("/")
        if last_slash != -1:
            masked = masked[: last_slash + 1] + DEMO_MASK_ARN_SESSION_NAME
    return masked


def get_demo_system_prompt_addition(name_mapping: dict[str, str]) -> str:
    """
    Generate system prompt instructions for demo mode.
    Tells the agent to use fake names in responses.
    """
    lines = [
        "",
        "DEMO MODE ACTIVE: You are in demo mode for a presentation.",
        "Replace all real AWS account names and IDs in your responses with fake/masked values:",
    ]

    if name_mapping:
        for real_name, fake_name in name_mapping.items():
            lines.append(f'- "{real_name}" → "{fake_name}"')
    else:
        lines.append("- Use generic names like Master_Account, Production, Staging, Development")

    lines.extend(
        [
            "- Account IDs should be shown as masked values like 000000000001 or ***",
            "- Never reveal real account names or IDs in your responses",
            "",
        ]
    )

    return "\n".join(lines)
