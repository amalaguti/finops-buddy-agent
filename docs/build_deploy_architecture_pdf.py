"""Render DEPLOY_AWS_ARCHITECTURE.md to PDF.

Uses **xhtml2pdf** (already a project dependency) so generation works on Windows
without WeasyPrint/GTK. If WeasyPrint is available (e.g. Linux CI), set
FINOPS_USE_WEASYPRINT=1 for higher-quality output.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

from markdown import markdown

DOCS = Path(__file__).resolve().parent
MD = DOCS / "DEPLOY_AWS_ARCHITECTURE.md"
PDF = DOCS / "DEPLOY_AWS_ARCHITECTURE.pdf"


def _strip_mermaid(raw: str) -> str:
    return re.sub(
        r"```mermaid\n.*?```\n",
        "<p><em>(Mermaid diagram omitted in PDF; see SVG figures in this document or the Markdown source.)</em></p>\n",
        raw,
        flags=re.DOTALL,
    )


def _build_html(fragment: str) -> str:
    css = """
    @page { size: A4; margin: 18mm; }
    body { font-family: Georgia, "Times New Roman", serif; font-size: 10.5pt;
           line-height: 1.45; color: #1a1a1a; }
    h1 { font-size: 18pt; border-bottom: 1px solid #cbd5e1; padding-bottom: 0.2em; }
    h2 { font-size: 13pt; margin-top: 1.2em; }
    h3 { font-size: 11pt; }
    code, pre { font-family: Consolas, "Courier New", monospace; font-size: 9pt;
                 background: #f1f5f9; }
    pre { padding: 0.5em; white-space: pre-wrap; word-break: break-word; }
    table { border-collapse: collapse; width: 100%; margin: 0.8em 0; font-size: 9.5pt; }
    th, td { border: 1px solid #94a3b8; padding: 0.35em 0.5em; text-align: left;
             vertical-align: top; }
    img { max-width: 100%; }
    hr { border: none; border-top: 1px solid #e2e8f0; margin: 1.5em 0; }
    """
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>FinOps Buddy AWS Reference Deployment</title>
<style>{css}</style>
</head>
<body>{fragment}</body>
</html>"""


def _write_pdf_xhtml2pdf(html: str) -> bool:
    from xhtml2pdf import pisa

    with PDF.open("wb") as out:
        status = pisa.CreatePDF(
            html,
            dest=out,
            encoding="utf-8",
            path=str(DOCS.resolve()),
        )
    return not status.err


def _write_pdf_weasyprint(html: str) -> None:
    from weasyprint import HTML

    base = DOCS.resolve().as_uri() + "/"
    HTML(string=html, base_url=base).write_pdf(PDF)


def main() -> int:
    if not MD.is_file():
        print("Missing", MD, file=sys.stderr)
        return 1
    raw = _strip_mermaid(MD.read_text(encoding="utf-8"))
    fragment = markdown(raw, extensions=["tables", "fenced_code", "nl2br"])
    html = _build_html(fragment)

    use_weasy = os.environ.get("FINOPS_USE_WEASYPRINT", "").lower() in ("1", "true", "yes")
    if use_weasy:
        try:
            _write_pdf_weasyprint(html)
            print(f"Wrote {PDF} (WeasyPrint)")
            return 0
        except Exception as e:  # noqa: BLE001
            print(f"WeasyPrint failed ({e}); falling back to xhtml2pdf.", file=sys.stderr)

    if _write_pdf_xhtml2pdf(html):
        print(f"Wrote {PDF} (xhtml2pdf)")
        return 0
    print("xhtml2pdf reported errors; PDF may be incomplete.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
