"""Pytest tests for artifact parsing (data URI images from assistant reply)."""

from finops_buddy.agent.artifacts import (
    artifact_export_from_file,
    parse_reply_data_uri_images,
    strip_non_data_uri_images,
)


def test_parse_reply_extracts_data_uri_images():
    """When reply contains markdown ![alt](data:image/png;base64,...), returns list of artifacts."""
    reply = (
        "Here is the chart:\n\n"
        "![Cost trend](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==)\n\n"
        "And another:\n\n"
        "![Breakdown](data:image/png;base64,QUJDREVGR0hJSktMTU5PUFFSU1RVVldYWVo=)"
    )
    artifacts = parse_reply_data_uri_images(reply)
    assert len(artifacts) == 2
    assert artifacts[0]["type"] == "chart"
    assert artifacts[0]["title"] == "Cost trend"
    assert artifacts[0]["content"].startswith("data:image/png;base64,")
    assert artifacts[1]["type"] == "chart"
    assert artifacts[1]["title"] == "Breakdown"
    assert artifacts[1]["content"].startswith("data:image/png;base64,")


def test_parse_reply_returns_empty_when_no_images():
    """When reply has no data URI images, returns empty list."""
    assert parse_reply_data_uri_images("Just text.") == []
    assert parse_reply_data_uri_images("![x](https://example.com/img.png)") == []
    assert parse_reply_data_uri_images("") == []
    assert parse_reply_data_uri_images(None) == []


def test_strip_non_data_uri_images_removes_placeholders():
    """strip_non_data_uri_images removes ![alt](non-data-uri) so UI does not show '[image not shown]'."""
    reply = "Here is the chart:\n\n![Chart](https://example.com/chart.png)\n\nDone."
    out = strip_non_data_uri_images(reply)
    assert "![Chart]" not in out or "data:image/" in out
    assert "https://example.com" not in out
    assert "Here is the chart:" in out and "Done." in out


def test_strip_non_data_uri_images_keeps_data_uri():
    """strip_non_data_uri_images leaves data:image/ images intact."""
    data_uri = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    reply = f"Text\n\n![Cost]({data_uri})\n\nMore."
    out = strip_non_data_uri_images(reply)
    assert data_uri in out
    assert "![Cost]" in out


def test_strip_non_data_uri_images_empty_or_none():
    """strip_non_data_uri_images returns reply unchanged when empty or no images."""
    assert strip_non_data_uri_images("") == ""
    assert strip_non_data_uri_images("No images here.") == "No images here."
    assert strip_non_data_uri_images(None) is None


def test_artifact_export_from_file_pdf_data_uri(tmp_path):
    """Exported PDF on disk becomes a data-URI artifact for the web UI basket."""
    p = tmp_path / "report.pdf"
    p.write_bytes(b"%PDF-1.4\nminimal")
    art = artifact_export_from_file(p)
    assert art is not None
    assert art["type"] == "pdf"
    assert art["title"] == "report.pdf"
    assert art["content"].startswith("data:application/pdf;base64,")


def test_artifact_export_from_file_xlsx_data_uri(tmp_path):
    """Exported xlsx on disk becomes a data-URI artifact."""
    p = tmp_path / "data.xlsx"
    p.write_bytes(b"PK\x03\x04fake")
    art = artifact_export_from_file(p)
    assert art is not None
    assert art["type"] == "excel"
    assert art["title"] == "data.xlsx"
    assert "spreadsheetml" in art["content"]
    assert art["content"].startswith("data:")
