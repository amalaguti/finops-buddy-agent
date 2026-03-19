"""Save/export for /print: scope, format, filename, exporters (txt, csv, pdf, xlsx)."""

from __future__ import annotations

import csv
import os
import re
import sys
from contextlib import contextmanager
from datetime import datetime
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


def _pdf_with_weasyprint(markdown_content: str, path: Path) -> tuple[bool, str]:
    """Render markdown to PDF with weasyprint (needs GTK/Cairo; often fails on Windows)."""
    import markdown as md_lib
    from weasyprint import HTML

    html = md_lib.markdown(
        markdown_content,
        extensions=["extra", "nl2br"],
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    HTML(string=f"<body>{html}</body>").write_pdf(path)
    return True, str(path)


def _pdf_with_xhtml2pdf(markdown_content: str, path: Path) -> tuple[bool, str]:
    """Render markdown to PDF with xhtml2pdf (pure Python, works on Windows)."""
    import markdown as md_lib
    from xhtml2pdf import pisa

    html = md_lib.markdown(
        markdown_content,
        extensions=["extra", "nl2br"],
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = f"""
    <!DOCTYPE html>
    <html><head><meta charset="utf-8"/>
    <style>
      body {{ font-family: Helvetica, sans-serif; font-size: 10pt; margin: 1in; }}
      h1 {{ font-size: 16pt; margin-top: 0; }}
      h2 {{ font-size: 13pt; border-bottom: 1px solid #ccc; margin-top: 1em; }}
      h3 {{ font-size: 11pt; margin-top: 0.8em; }}
      table {{ border-collapse: collapse; width: 100%; margin: 0.5em 0; }}
      th, td {{ border: 1px solid #ddd; padding: 4px 8px; text-align: left; }}
      th {{ background: #f5f5f5; }}
    </style></head><body>{html}</body></html>
    """
    with path.open("wb") as dest:
        status = pisa.CreatePDF(doc, dest, encoding="utf-8")
    if status.err:
        return False, f"xhtml2pdf failed: {status.err}"
    return True, str(path)


def _escape_reportlab(s: str) -> str:
    """Escape text for reportlab Paragraph/XML (avoid invalid markup)."""
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _pdf_with_reportlab(markdown_content: str, path: Path) -> tuple[bool, str]:
    """Render markdown to PDF with reportlab (pure Python, no GTK)."""
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(path),
        rightMargin=inch,
        leftMargin=inch,
        topMargin=inch,
        bottomMargin=inch,
    )
    styles = getSampleStyleSheet()
    story = []
    table_pattern = re.compile(r"^\s*\|.+\|\s*$")
    for block in re.split(r"\n\s*\n", markdown_content):
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
                t.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), (0.9, 0.9, 0.9)),
                            ("GRID", (0, 0), (-1, -1), 0.5, (0.5, 0.5, 0.5)),
                            ("FONTSIZE", (0, 0), (-1, -1), 9),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ]
                    )
                )
                story.append(t)
                story.append(Spacer(1, 12))
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


def export_pdf_fallback(markdown_content: str, path: Path) -> tuple[bool, str]:
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
                ok, msg = fn(markdown_content, path)
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


def export_pdf(markdown_content: str, path: Path) -> tuple[bool, str]:
    """
    Export markdown to PDF: try in-process fallback first (weasyprint/xhtml2pdf/reportlab),
    then PDF MCP only if fallback fails. Using in-process first avoids the PDF MCP server
    writing WeasyPrint errors to its stdout and breaking the JSON-RPC channel.
    Returns (success, message).
    """
    ok, msg = export_pdf_fallback(markdown_content, path)
    if ok:
        return True, msg
    from finops_buddy.settings import get_pdf_mcp_enabled

    if get_pdf_mcp_enabled():
        ok, msg = export_pdf_via_mcp(markdown_content, path)
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
) -> None:
    """
    Run the /print save flow: prompt for scope and format, build content, export to file.

    agent: Used only when scope is "summary" (one call to get summary text).
    input_func: Callable[[], str] for reading user input (default: builtin input).
    print_func: Callable[[str], None] for output (default: builtin print).
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
        ok, msg = export_pdf(markdown, path)
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
