"""Save/export for /print: scope, format, filename, exporters (txt, csv, pdf, xlsx)."""

from __future__ import annotations

import csv
import os
import re
import sys
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

# Scope identifiers for content selection
SCOPE_FULL = "full"
SCOPE_QA = "qa"
SCOPE_SUMMARY = "summary"
SCOPE_LAST = "last"

# Format identifiers
FORMAT_TXT = "txt"
FORMAT_PDF = "pdf"
FORMAT_CSV = "csv"
FORMAT_XLSX = "xlsx"

DEFAULT_TITLE = "conversation"
MAX_TITLE_LENGTH = 50

# Print CSS aligned with markdown-to-pdf-guide.md (A4, FinOps/AWS-adjacent palette).
PRINT_PDF_CSS = """
  @page { size: A4; margin: 2cm; }
  body { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; font-size: 11pt;
         color: #1a1a1a; line-height: 1.45; margin: 0; }
  h1 { color: #232f3e; border-bottom: 3px solid #ff9900; padding-bottom: 8px; font-size: 22px;
       margin: 0 0 12px 0; }
  h2 { color: #232f3e; border-bottom: 1px solid #ddd; padding-bottom: 5px; margin: 18px 0 10px 0;
       font-size: 16px; }
  h3 { color: #545b64; font-size: 13px; margin: 14px 0 8px 0; }
  p { margin: 0 0 8px 0; }
  ul, ol { margin: 6px 0 10px 0; padding-left: 22px; }
  li { margin: 2px 0; }
  table { border-collapse: collapse; width: 100%; margin: 10px 0; font-size: 10pt; }
  th { background-color: #232f3e; color: #ffffff; padding: 8px 10px; text-align: left; }
  td { padding: 6px 10px; border-bottom: 1px solid #ddd; }
  tr:nth-child(even) { background-color: #f7f7f7; }
  strong { color: #d13212; }
  blockquote { background: #fff3cd; border-left: 4px solid #ff9900; padding: 10px 15px;
               margin: 12px 0; }
  hr { border: none; border-top: 1px solid #ddd; margin: 16px 0; }
  a { color: #0073bb; }
  code { background: #f1f1f1; padding: 1px 4px; border-radius: 3px; font-size: 10pt; }
  pre { background: #f5f5f5; padding: 10px; border-radius: 4px; font-size: 9pt; overflow: auto; }
"""


@dataclass
class PdfExportCover:
    """Optional cover block for PDF exports (metadata only — no invented AWS data)."""

    profile_name: str | None = None
    exported_at: datetime | None = None


def _slugify(text: str) -> str:
    """Slugify for filename: lowercase, replace non-alnum with '-', collapse dashes."""
    if not text or not text.strip():
        return ""
    s = text.strip().lower()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[-\s]+", "-", s)
    return s.strip("-")[:MAX_TITLE_LENGTH] if s else ""


def _first_user_message(conversation: list[str]) -> str:
    """Return the first user message content (without 'User:' prefix) for title derivation."""
    for line in conversation:
        if line.startswith("User:"):
            return line[5:].strip()
    return ""


def build_content_for_scope(
    conversation: list[str],
    scope: str,
    summary_text: str | None = None,
) -> tuple[str, str, list[tuple[int, str, str]]]:
    """
    Build plain text, markdown, and rows (turn, role, content) for the given scope.

    Returns (plain_text, markdown_text, rows).
    """
    if scope == SCOPE_SUMMARY and summary_text is not None:
        plain = summary_text
        md = summary_text
        rows = [(1, "summary", summary_text)]
        return plain, md, rows

    # Parse conversation into turns
    turns: list[tuple[int, str, str]] = []
    for i, line in enumerate(conversation):
        line = line.strip()
        if line.startswith("User:"):
            turns.append((i // 2 + 1, "User", line[5:].strip()))
        elif line.startswith("Agent:"):
            turns.append((i // 2 + 1, "Agent", line[6:].strip()))

    if scope == SCOPE_LAST:
        if not turns:
            plain = md = ""
            rows = []
        else:
            last = turns[-1]
            plain = f"{last[1]}: {last[2]}"
            md = f"## {last[1]}\n\n{last[2]}"
            rows = [last]
        return plain, md, rows

    # Full or Q&A: all turns (same content; Q&A is just presentation)
    plain_parts = [f"{role}: {content}" for _, role, content in turns]
    plain = "\n\n".join(plain_parts)

    md_parts = [f"## {role}\n\n{content}" for _, role, content in turns]
    md = "\n\n".join(md_parts)

    return plain, md, turns


def generate_output_filename(conversation: list[str], ext: str) -> str:
    """Generate filename: timestamp-conversation_title.<ext>. Uses cwd for directory."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    first = _first_user_message(conversation)
    title = _slugify(first) if first else DEFAULT_TITLE
    safe_ext = ext.lstrip(".")
    return f"{ts}-{title}.{safe_ext}"


def get_output_path(filename: str, output_dir: Path | None = None) -> Path:
    """Return full path for the output file. Default directory is cwd."""
    base = output_dir or Path.cwd()
    return base / filename


def normalize_markdown_pdf_spacing(text: str) -> str:
    """Collapse excessive blank lines so PDFs do not get runaway vertical gaps."""
    text = text.replace("\r\n", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _apply_pdf_cover(markdown_content: str, cover: PdfExportCover | None) -> str:
    if cover is None:
        return markdown_content
    ts = cover.exported_at or datetime.now(timezone.utc)
    stamp = ts.strftime("%Y-%m-%d %H:%M:%S UTC")
    lines = [
        "# FinOps Buddy — conversation export",
        "",
        f"**Exported:** {stamp}",
    ]
    if cover.profile_name:
        lines.append(f"**Profile:** {cover.profile_name}")
    lines.extend(["", "---", "", markdown_content])
    return "\n".join(lines)


def _markdown_for_pdf(markdown_content: str, cover: PdfExportCover | None) -> str:
    return normalize_markdown_pdf_spacing(_apply_pdf_cover(markdown_content, cover))


def _markdown_to_pdf_body_html(markdown: str) -> str:
    import markdown as md_lib

    return md_lib.markdown(
        markdown,
        extensions=["tables", "fenced_code"],
    )


def _wrap_print_html_document(body_html: str) -> str:
    return (
        '<!DOCTYPE html>\n<html><head><meta charset="utf-8"/>'
        f"<style>{PRINT_PDF_CSS}</style></head><body>{body_html}</body></html>"
    )


def build_pdf_html_document(
    markdown_content: str,
    *,
    cover: PdfExportCover | None = None,
) -> str:
    """
    Build a full HTML document string for PDF rendering (WeasyPrint / xhtml2pdf).
    Used by /print and tests; applies cover, spacing normalization, and print CSS.
    """
    md = _markdown_for_pdf(markdown_content, cover)
    body = _markdown_to_pdf_body_html(md)
    return _wrap_print_html_document(body)


def export_txt(content: str, path: Path) -> None:
    """Write content as plain text to path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def export_csv(rows: list[tuple[int, str, str]], path: Path) -> None:
    """Write rows as CSV with columns turn, role, content."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["turn", "role", "content"])
        w.writerows(rows)


def export_pdf_via_mcp(markdown_content: str, path: Path) -> tuple[bool, str]:
    """
    Call PDF MCP (md-to-pdf-mcp) to convert markdown to PDF at path.
    Input is Markdown only (same normalized/covered string as the in-process pipeline);
    MCP styling may differ from FinOps Buddy's styled HTML path.
    Returns (success, message). On success message is the path as string.
    """
    from finops_buddy.settings import (
        get_pdf_mcp_command,
        get_pdf_mcp_enabled,
    )

    if not get_pdf_mcp_enabled():
        return False, "PDF MCP is disabled. Enable it in config or use format txt/csv."

    try:
        import asyncio

        from mcp import StdioServerParameters
        from mcp.client.session import ClientSession
        from mcp.client.stdio import stdio_client

        command, args = get_pdf_mcp_command()
        params = StdioServerParameters(command=command, args=args)

        async def _run() -> tuple[bool, str]:
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.call_tool(
                        "convert_markdown_to_pdf",
                        arguments={
                            "markdown": markdown_content,
                            "outputFilename": str(path),
                        },
                    )
                    if getattr(result, "isError", False):
                        err = getattr(result, "content", result)
                        return False, f"PDF MCP error: {err}"
                    # Success: tool may have written to outputFilename
                    if path.exists():
                        return True, str(path)
                    # Some MCPs return file content in result
                    content = getattr(result, "content", [])
                    if content and isinstance(content, list):
                        for block in content:
                            if hasattr(block, "path") and block.path:
                                return True, str(block.path)
                            if hasattr(block, "text"):
                                raw = block.text
                                path.write_bytes(
                                    raw.encode("utf-8") if isinstance(raw, str) else raw
                                )
                                return True, str(path)
                    return False, "PDF MCP did not return a file path or content."

        return asyncio.run(_run())
    except ImportError as e:
        return False, f"PDF MCP requires mcp package: {e}"
    except Exception as e:
        return False, f"PDF export failed: {e}"


def _pdf_with_weasyprint(
    markdown_content: str,
    path: Path,
    *,
    cover: PdfExportCover | None = None,
) -> tuple[bool, str]:
    """Render Markdown to PDF with WeasyPrint (needs GTK/Cairo; often fails on Windows)."""
    from weasyprint import HTML

    html_document = build_pdf_html_document(markdown_content, cover=cover)
    path.parent.mkdir(parents=True, exist_ok=True)
    HTML(string=html_document).write_pdf(path)
    return True, str(path)


def _pdf_with_xhtml2pdf(
    markdown_content: str,
    path: Path,
    *,
    cover: PdfExportCover | None = None,
) -> tuple[bool, str]:
    """Render Markdown to PDF with xhtml2pdf (pure Python; same HTML+CSS as WeasyPrint)."""
    from xhtml2pdf import pisa

    html_document = build_pdf_html_document(markdown_content, cover=cover)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as dest:
        status = pisa.CreatePDF(html_document, dest, encoding="utf-8")
    if status.err:
        return False, f"xhtml2pdf failed: {status.err}"
    return True, str(path)


def _escape_reportlab(s: str) -> str:
    """Escape text for reportlab Paragraph/XML (avoid invalid markup)."""
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _pdf_with_reportlab(
    markdown_content: str,
    path: Path,
    *,
    cover: PdfExportCover | None = None,
) -> tuple[bool, str]:
    """
    Render Markdown to PDF with ReportLab (simplified fallback — not full Markdown/CSS parity).
    """
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    md = _markdown_for_pdf(markdown_content, cover)
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(path),
        rightMargin=inch * 0.75,
        leftMargin=inch * 0.75,
        topMargin=inch * 0.75,
        bottomMargin=inch * 0.75,
    )
    styles = getSampleStyleSheet()
    story = []
    header_bg = colors.HexColor("#232f3e")
    header_fg = colors.HexColor("#ffffff")
    grid_color = colors.HexColor("#dddddd")
    zebra = colors.HexColor("#f7f7f7")
    table_pattern = re.compile(r"^\s*\|.+\|\s*$")
    for block in re.split(r"\n\s*\n", md):
        block = block.strip()
        if not block:
            continue
        lines = block.split("\n")
        if all(table_pattern.match(ln) for ln in lines):
            rows = []
            for ln in lines:
                parts = ln.split("|")
                cells = [_escape_reportlab(c.strip()) for c in parts[1:-1] if len(parts) > 2]
                if not cells:
                    continue
                if all(re.match(r"^[\s\-:]+$", c) for c in cells):
                    continue
                rows.append(cells)
            if rows:
                t = Table(rows)
                nrows = len(rows)
                style_cmds = [
                    ("BACKGROUND", (0, 0), (-1, 0), header_bg),
                    ("TEXTCOLOR", (0, 0), (-1, 0), header_fg),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.5, grid_color),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
                if nrows > 1:
                    style_cmds.append(
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, zebra]),
                    )
                t.setStyle(TableStyle(style_cmds))
                story.append(t)
                story.append(Spacer(1, 10))
            continue
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.startswith("# "):
                story.append(Paragraph(_escape_reportlab(line[2:].strip()), styles["Title"]))
            elif line.startswith("## "):
                story.append(Paragraph(_escape_reportlab(line[3:].strip()), styles["Heading1"]))
            elif line.startswith("### "):
                story.append(Paragraph(_escape_reportlab(line[4:].strip()), styles["Heading2"]))
            elif line.startswith("- ") or line.startswith("* "):
                story.append(Paragraph("&bull; " + _escape_reportlab(line[2:]), styles["Normal"]))
            else:
                story.append(Paragraph(_escape_reportlab(line), styles["Normal"]))
        story.append(Spacer(1, 8))
    doc.build(story)
    return True, str(path)


@contextmanager
def _suppress_stdout_stderr():
    """Redirect stdout/stderr to devnull so PDF libs don't break MCP or spam terminal."""
    old_out, old_err = sys.stdout, sys.stderr
    try:
        with open(os.devnull, "w", encoding="utf-8") as devnull:
            sys.stdout = sys.stderr = devnull
            yield
    finally:
        sys.stdout, sys.stderr = old_out, old_err


def export_pdf_fallback(
    markdown_content: str,
    path: Path,
    *,
    cover: PdfExportCover | None = None,
) -> tuple[bool, str]:
    """
    Convert markdown to PDF in-process: try weasyprint, then xhtml2pdf, then reportlab.
    WeasyPrint needs GTK/Cairo (often fails on Windows); xhtml2pdf and reportlab are pure Python.
    Stdout/stderr are suppressed during rendering so library messages don't pollute terminal or MCP.
    Returns (success, message).
    """
    for name, fn in [
        ("weasyprint", _pdf_with_weasyprint),
        ("xhtml2pdf", _pdf_with_xhtml2pdf),
        ("reportlab", _pdf_with_reportlab),
    ]:
        try:
            with _suppress_stdout_stderr():
                ok, msg = fn(markdown_content, path, cover=cover)
            if ok:
                return True, msg
            if name == "weasyprint":
                continue
            return False, msg
        except ImportError:
            continue
        except Exception as e:
            if "libgobject" in str(e).lower() or "cairo" in str(e).lower():
                continue
            return False, f"PDF fallback ({name}) failed: {e}"
    return False, "PDF fallback failed: need weasyprint, xhtml2pdf, or reportlab."


def export_pdf(
    markdown_content: str,
    path: Path,
    *,
    cover: PdfExportCover | None = None,
) -> tuple[bool, str]:
    """
    Export markdown to PDF: try styled in-process pipeline first (weasyprint/xhtml2pdf/reportlab),
    then PDF MCP only if fallback fails. MCP receives the same Markdown as the styled pipeline
    (after cover + spacing normalization), not the HTML document.
    Returns (success, message).
    """
    ok, msg = export_pdf_fallback(markdown_content, path, cover=cover)
    if ok:
        return True, msg
    from finops_buddy.settings import get_pdf_mcp_enabled

    if get_pdf_mcp_enabled():
        md_for_mcp = _markdown_for_pdf(markdown_content, cover)
        ok, msg = export_pdf_via_mcp(md_for_mcp, path)
        if ok:
            return True, msg
    return False, msg


def export_xlsx_openpyxl(rows: list[tuple[int, str, str]], path: Path) -> None:
    """Write conversation rows to an xlsx file using openpyxl (built-in fallback)."""
    export_xlsx_from_table(
        [["turn", "role", "content"]] + [[r[0], r[1], r[2]] for r in rows],
        path,
        sheet_name="Conversation",
    )


def export_xlsx_from_table(
    rows: list[list],
    path: Path,
    sheet_name: str = "Export",
) -> None:
    """Write any list of rows (first row = header) to an xlsx file using openpyxl."""
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    if ws is not None:
        ws.title = sheet_name[:31]  # Excel sheet name limit
    else:
        ws = wb.create_sheet(sheet_name[:31])
    for row in rows:
        ws.append([cell for cell in row])
    wb.save(path)


def export_xlsx_via_mcp(rows: list[tuple[int, str, str]], path: Path) -> tuple[bool, str]:
    """
    Call Excel MCP when it exposes create_workbook/write_worksheet; else use openpyxl.
    Returns (success, message).
    """
    from finops_buddy.settings import get_excel_mcp_enabled

    # If MCP enabled, try it first
    if get_excel_mcp_enabled():
        ok, msg = _try_excel_mcp(rows, path)
        if ok:
            return True, msg
        # MCP failed or wrong tools: fall back to openpyxl
        try:
            export_xlsx_openpyxl(rows, path)
            return True, str(path)
        except Exception as e:
            return False, f"Excel export failed (MCP: {msg}; openpyxl: {e})"

    # MCP disabled: use openpyxl only
    try:
        export_xlsx_openpyxl(rows, path)
        return True, str(path)
    except ImportError:
        return False, "Excel MCP is disabled. Enable it in config or install openpyxl for xlsx."
    except Exception as e:
        return False, f"Excel export failed: {e}"


def _try_excel_mcp(rows: list[tuple[int, str, str]], path: Path) -> tuple[bool, str]:
    """Use Excel MCP if it exposes create_workbook and write_worksheet. Else (False, reason)."""
    try:
        import asyncio

        from mcp import StdioServerParameters
        from mcp.client.session import ClientSession
        from mcp.client.stdio import stdio_client

        from finops_buddy.settings import get_excel_mcp_command

        command, args = get_excel_mcp_command()
        params = StdioServerParameters(command=command, args=args)
        data = [["turn", "role", "content"]]
        data.extend(list(r) for r in rows)

        async def _run() -> tuple[bool, str]:
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    tools_result = await session.list_tools()
                    tools_list = getattr(tools_result, "tools", None) or []
                    tool_names = [
                        getattr(t, "name", t.get("name") if isinstance(t, dict) else "")
                        for t in tools_list
                    ]
                    create_tool = "create_workbook" if "create_workbook" in tool_names else None
                    write_tool = "write_worksheet" if "write_worksheet" in tool_names else None
                    if not create_tool or not write_tool:
                        return False, "Excel MCP does not expose create_workbook/write_worksheet."
                    create_result = await session.call_tool(
                        create_tool,
                        arguments={"file_path": str(path)},
                    )
                    if getattr(create_result, "isError", False):
                        err = getattr(create_result, "content", create_result)
                        return False, f"Excel MCP create_workbook: {err}"
                    write_result = await session.call_tool(
                        write_tool,
                        arguments={
                            "file_path": str(path),
                            "sheet_name": "Conversation",
                            "data": data,
                        },
                    )
                    if getattr(write_result, "isError", False):
                        err = getattr(write_result, "content", write_result)
                        return False, f"Excel MCP write_worksheet: {err}"
                    return True, str(path)

        return asyncio.run(_run())
    except ImportError as e:
        return False, f"Excel MCP requires mcp package: {e}"
    except Exception as e:
        return False, f"Excel MCP error: {e}"


def parse_scope_input(raw: str) -> str | None:
    """Parse user input for scope: 1/full, 2/qa, 3/summary, 4/last. Returns scope id or None."""
    s = (raw or "").strip().lower()
    if s in ("1", "full", "entire", "all"):
        return SCOPE_FULL
    if s in ("2", "qa", "q&a", "questions", "answers"):
        return SCOPE_QA
    if s in ("3", "summary", "summarized", "summarise"):
        return SCOPE_SUMMARY
    if s in ("4", "last", "last response", "last only"):
        return SCOPE_LAST
    return None


def parse_format_input(raw: str) -> str | None:
    """Parse user input for format: txt, pdf, csv, xlsx. Returns format id or None."""
    s = (raw or "").strip().lower()
    if s in ("txt", "text", "1"):
        return FORMAT_TXT
    if s in ("pdf", "2"):
        return FORMAT_PDF
    if s in ("csv", "3"):
        return FORMAT_CSV
    if s in ("xlsx", "excel", "4"):
        return FORMAT_XLSX
    return None


def run_print_flow(
    conversation: list[str],
    agent: object,
    *,
    output_dir: Path | None = None,
    input_func: object = None,
    print_func: object = None,
    profile_name: str | None = None,
) -> None:
    """
    Run the /print save flow: prompt for scope and format, build content, export to file.

    agent: Used only when scope is "summary" (one call to get summary text).
    input_func: Callable[[], str] for reading user input (default: builtin input).
    print_func: Callable[[str], None] for output (default: builtin print).
    profile_name: Optional AWS profile (from CLI); included on PDF cover when exporting PDF.
    """
    inp = input_func if callable(input_func) else input
    out = print_func if callable(print_func) else print

    if not conversation:
        out("No conversation to save. Send a message first, then use /print.")
        return

    out("What do you want to save?")
    out("  1 = entire conversation  2 = Q&A only  3 = summarized  4 = last response only")
    raw_scope = inp("Scope (1-4 or name): ").strip()
    scope = parse_scope_input(raw_scope)
    if not scope:
        out("Unknown scope. Use 1, 2, 3, or 4 (or full, qa, summary, last).")
        return

    summary_text = None
    if scope == SCOPE_SUMMARY:
        out("Summarizing conversation...")
        try:
            prompt = (
                "Summarize the following conversation concisely in a few paragraphs. "
                "Do not add preamble; output only the summary.\n\n" + "\n\n".join(conversation)
            )
            result = agent(prompt)
            summary_text = str(result).strip() if result else ""
        except Exception as e:
            out(f"Summary failed: {e}. Try another scope or format.")
            return

    out("Format: 1 = txt  2 = pdf  3 = csv  4 = xlsx")
    raw_fmt = inp("Format (1-4 or name): ").strip()
    fmt = parse_format_input(raw_fmt)
    if not fmt:
        out("Unknown format. Use 1, 2, 3, or 4 (or txt, pdf, csv, xlsx).")
        return

    plain, markdown, rows = build_content_for_scope(conversation, scope, summary_text)
    ext = fmt
    filename = generate_output_filename(conversation, ext)
    path = get_output_path(filename, output_dir)

    if fmt == FORMAT_TXT:
        export_txt(plain, path)
        out(f"Saved to {path}")
        return
    if fmt == FORMAT_CSV:
        export_csv(rows, path)
        out(f"Saved to {path}")
        return
    if fmt == FORMAT_PDF:
        cover = PdfExportCover(profile_name=profile_name.strip() if profile_name else None)
        ok, msg = export_pdf(markdown, path, cover=cover)
        if ok:
            out(f"Saved to {msg}")
        else:
            out(msg)
        return
    if fmt == FORMAT_XLSX:
        ok, msg = export_xlsx_via_mcp(rows, path)
        if ok:
            out(f"Saved to {msg}")
        else:
            out(msg)
