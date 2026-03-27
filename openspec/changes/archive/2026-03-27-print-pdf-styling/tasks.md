# print-pdf-styling — Tasks

**Branch:** Do not implement on `main`. Use a feature branch (e.g. `feature/print-pdf-styling`).

## 1. Implementation — PDF pipeline

- [x] 1.1 Add a single **Markdown → styled HTML document** builder in `conversation_printer.py` (or a small dedicated module), using CSS aligned with `markdown-to-pdf-guide.md` (A4 `@page`, typography, table header/zebra, code/blockquote links).
- [x] 1.2 Enable **`tables`** (and **`fenced_code`** as needed) for PDF Markdown conversion; disable or narrowly scope **`nl2br`**; add **blank-line normalization** before conversion to reduce runaway vertical gaps (per design).
- [x] 1.3 Update **`_pdf_with_weasyprint`** and **`_pdf_with_xhtml2pdf`** to render the **same** full HTML string from 1.1 (no bare `<body>`-only WeasyPrint path).
- [x] 1.4 Improve **`_pdf_with_reportlab`** table/heading styling toward the same palette (document as simplified fallback, not full Markdown parity).
- [x] 1.5 Confirm **`export_pdf`** / **`export_pdf_via_mcp`** behavior matches the spec: in-process styled path first, MCP when enabled after fallbacks fail; adjust docs/comments if MCP input remains Markdown-only.
- [x] 1.6 Optionally prepend **PDF cover metadata** (title, timestamp, profile when available) per spec; gate behind minimal logic so tests stay deterministic.

## 2. Tests

- [x] 2.1 Extend **`tests/test_conversation_printer.py`**: scenarios for **styled HTML** (embedded `<style>`, `@page` or body rules), **pipe table → `<table>`**, **normalization** / spacing behavior, optional cover block; one test per new **#### Scenario** where practical.
- [x] 2.2 Run **`poetry run ruff check .`** and **`poetry run ruff format .`**; fix any issues.
- [x] 2.3 Run **`poetry run bandit -c pyproject.toml -r src/`**; fix medium+ findings.
- [x] 2.4 Run **`poetry run pytest`** for the project (or targeted tests) until green.
- [x] 2.5 Run **`poetry run pip-audit`** once; address or document findings.

## 3. Documentation and settings

- [x] 3.1 Update **`docs/CONFIGURATION.md`**: PDF pipeline order, styled in-process output, WeasyPrint vs xhtml2pdf vs reportlab vs MCP, and any new **`FINOPS_*`** variables if custom CSS or toggles are added.
- [x] 3.2 If new settings keys are introduced, update **`config/settings.yaml`** as a commented template with placeholders. *(No new keys in this change — N/A.)*
- [x] 3.3 Add a short pointer in root **`README.md`** documentation table only if new users need a direct link to `/print` PDF behavior (keep README slim).

## 4. OpenSpec sync (on apply)

- [x] 4.1 After implementation, merge **`openspec/changes/print-pdf-styling/specs/conversation-printer/spec.md`** into **`openspec/specs/conversation-printer/spec.md`** (create canonical spec if missing), per project OpenSpec sync rules.
