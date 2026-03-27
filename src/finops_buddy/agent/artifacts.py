"""Parse assistant reply for embedded data URI images (e.g. charts) for artifact events."""

from __future__ import annotations

import base64
import re
from pathlib import Path

# Match markdown image with data URI: ![alt](data:image/png;base64,...)
_DATA_URI_IMAGE_PATTERN = re.compile(r"!\[([^\]]*)\]\((data:image/[^;]+;base64,[A-Za-z0-9+/=]+)\)")

# Match any markdown image: ![alt](url) — used to strip non–data-URI placeholders
_ANY_IMAGE_PATTERN = re.compile(r"!\[([^\]]*)\]\(([^)]*)\)")


def parse_reply_data_uri_images(reply: str) -> list[dict[str, str]]:
    """
    Extract embedded data URI images from assistant reply markdown.

    Returns a list of dicts: {"type": "chart", "title": alt text, "content": data URI}.
    """
    if not reply or not isinstance(reply, str):
        return []
    out = []
    for m in _DATA_URI_IMAGE_PATTERN.finditer(reply):
        alt = (m.group(1) or "").strip() or "Chart"
        content = m.group(2) or ""
        if content.startswith("data:image/"):
            out.append({"type": "chart", "title": alt, "content": content})
    return out


def strip_non_data_uri_images(reply: str) -> str:
    """
    Remove from reply any markdown images whose URL is not a data:image/ URI.
    Keeps data-URI images; removes placeholders like ![Chart](https://...) so the
    UI does not show "[image not shown]" for model-generated placeholders.
    """
    if not reply or not isinstance(reply, str):
        return reply

    def replace(match: re.Match[str]) -> str:
        url = (match.group(2) or "").strip()
        if url.startswith("data:image/"):
            return match.group(0)
        return ""

    return _ANY_IMAGE_PATTERN.sub(replace, reply)


# Web UI /chat SSE: cap embedded file payloads (base64 in JSON).
_MAX_EXPORT_ARTIFACT_BYTES = 10 * 1024 * 1024


def artifact_export_from_file(
    path: Path | str,
    *,
    max_bytes: int = _MAX_EXPORT_ARTIFACT_BYTES,
) -> dict[str, str] | None:
    """
    Build an artifact dict {type, title, content} with a data: URI for browser download.

    Used when export_to_pdf / export_to_excel write a file on the server; the hook reads
    the file and attaches it to the Artifacts basket. Returns None if missing, too large,
    or unsupported extension.
    """
    p = Path(path)
    if not p.is_file():
        return None
    suffix = p.suffix.lower()
    if suffix == ".pdf":
        mime = "application/pdf"
        kind = "pdf"
    elif suffix == ".xlsx":
        mime = (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        kind = "excel"
    else:
        return None
    try:
        raw = p.read_bytes()
    except OSError:
        return None
    if len(raw) > max_bytes:
        return None
    b64 = base64.standard_b64encode(raw).decode("ascii")
    return {
        "type": kind,
        "title": p.name,
        "content": f"data:{mime};base64,{b64}",
    }
