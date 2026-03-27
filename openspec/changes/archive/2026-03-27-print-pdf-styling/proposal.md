# Print PDF Styling — Proposal

## Why

The existing **`/print`** flow (see archived change `2026-03-11-conversation-printer`) saves conversations to several formats; **PDF output is perceived as low quality**: tables look crude, typography and spacing feel “raw,” and line/paragraph gaps are excessive compared to professionally styled reports.

A separate reference document in this repo, **`markdown-to-pdf-guide.md`**, describes a proven pipeline—**Markdown → HTML (with table support) → fully styled HTML document → PDF**—that produces **deterministic, print-ready** output using **`markdown` + `weasyprint`** and an embedded **CSS** layer (A4 `@page`, heading hierarchy, zebra tables, tuned font sizes). A concrete quality bar is the sample **`cost-anomaly-report-2026-03-27.md`** / PDF pair (Kiro-generated): dense, readable tables, consistent headings, and controlled vertical rhythm.

Today’s implementation in `src/finops_buddy/agent/conversation_printer.py` does not follow that approach end-to-end:

- **WeasyPrint path** converts Markdown to HTML but wraps it in a **bare `<body>` fragment with no document shell or stylesheet**, so the PDF inherits browser-default spacing and unstyled tables.
- **Fallback order** tries WeasyPrint, then **xhtml2pdf** with only **minimal** CSS (light gray headers, basic borders)—far from the guide’s professional theme.
- **Markdown extensions** use **`extra` + `nl2br`** rather than the guide’s emphasis on **`tables`** for GFM-style pipe tables; **`nl2br`** can also **inflate vertical spacing** when combined with conversation text that already contains blank lines.
- **PDF MCP** (`md-to-pdf-mcp`) may run with its own defaults; when used, styling may still not match FinOps Buddy’s desired “report” look unless we pass parameters or prefer the in-house styled pipeline.

Users expect **`/print` → PDF** to look **professional and on par** with well-styled Markdown exports (similar to the guide and the attached anomaly report), not like a plain HTML dump.

## What Changes

- **Adopt a single “conversation PDF” presentation layer** aligned with **`markdown-to-pdf-guide.md`**:
  - **Stage 1:** Parse Markdown with extensions appropriate for chat exports—at minimum **`tables`** for pipe tables; explicitly validate behavior for fenced code, lists, and emphasis. Revisit **`nl2br`**: use only if required for fidelity, or **normalize** user/agent text (e.g. collapse redundant blank lines) **before** Markdown conversion to avoid oversized paragraph gaps.
  - **Stage 2:** Wrap the generated HTML in a **full document** (`<!DOCTYPE html>`, `<head>`, embedded `<style>`) using a **maintained default stylesheet** (FinOps/AWS-inspired palette acceptable, as in the guide: A4 margins, heading underlines, dark table headers, zebra rows, compact table font size, sensible `line-height` on `body`, styled `blockquote`/`code`/`hr`/`a`).
  - **Stage 3:** Render with **WeasyPrint** when available; apply the **same HTML+CSS** string to **xhtml2pdf** where CSS support allows, with **documented degradation** (e.g. selectors not supported) and tests or manual checklist for Windows.
- **Unify styling across PDF backends** where feasible: avoid divergent “bare body” vs “wrapped + CSS” behavior between WeasyPrint and xhtml2pdf.
- **Optional document front-matter** for PDF only: e.g. title line (“FinOps Buddy — conversation export”), export timestamp, optional profile/context—so the first page reads like a report cover block, similar in spirit to the sample Markdown’s header metadata (without inventing data the app does not already have).
- **MCP integration policy:** Define whether **`convert_markdown_to_pdf`** receives **pre-styled full HTML** (if the tool accepts HTML), only raw Markdown (then MCP styling remains unknown), or whether **MCP is skipped** when a local styled pipeline succeeds—so “professional PDF” is **predictable** for `/print`.
- **ReportLab fallback:** Keep as last resort for environments without WeasyPrint/xhtml2pdf, but **narrow the gap** (shared style constants, better table styling) or **clearly document** that it is a simplified renderer—not parity with Markdown+CSS.
- **Documentation:** Update **`docs/CONFIGURATION.md`** (and pointer in root **README** table if needed) to describe PDF quality expectations, dependency notes (WeasyPrint system libs vs pure-Python fallback), and any new **`FINOPS_`** toggles if we expose theme or “compact spacing” options.
- **Tests:** Pytest scenarios for: Markdown with **pipe tables** renders `<table>` with header row; **no runaway vertical whitespace** from typical `User:`/`Agent:` turn layout; styled HTML contains expected **CSS class or rule markers** (or snapshot of normalized HTML wrapper); optional smoke test that a PDF file is non-empty and parses (without pixel comparison).

## Capabilities

### New Capabilities

- None (this is a **quality and implementation** upgrade within the same user-facing feature).

### Modified Capabilities

- **conversation-printer** (delta spec to add under this change): Extend requirements for **PDF export** so that:
  - Exported PDFs use a **document-level stylesheet** with **print-oriented** typography and **table** styling (not unstyled HTML defaults).
  - Markdown conversion **enables table parsing** for standard pipe tables used in chat content.
  - **Spacing** defaults are **tightened** versus the current implementation (explicit scenarios: multi-turn Q&A, message containing markdown tables).
  - Fallback chain behavior (WeasyPrint → xhtml2pdf → reportlab → MCP) remains, but **normative text** defines **minimum visual parity** for the primary path(s) and **honest limits** for fallbacks.

*Note:* If **`conversation-printer`** exists only under `openspec/changes/archive/`, create **`openspec/changes/print-pdf-styling/specs/conversation-printer/spec.md`** as a delta and merge into **`openspec/specs/`** on apply (or add **`openspec/specs/conversation-printer/spec.md`** if the project adopts main specs for this capability).

## Impact

| Area | Impact |
|------|--------|
| **Code** | `src/finops_buddy/agent/conversation_printer.py` (PDF helpers, markdown extensions, shared HTML/CSS builder); possibly small helpers for CSS constant(s) or template; optional `export_to_pdf` tools path if agent uses same renderer. |
| **Dependencies** | Prefer **existing** `markdown`, `weasyprint`, `xhtml2pdf`, `reportlab`; add none unless the chosen pipeline requires an extra extension package (avoid if possible). |
| **Config** | Optional new settings for **custom CSS path** or **compact mode** (`FINOPS_*` only)—only if product wants user overrides; default can remain zero-config. |
| **Docker / CI** | Align container OS packages with WeasyPrint where PDF quality matters (may already be partially addressed in prior deployment specs). |
| **Docs** | `docs/CONFIGURATION.md`; optional short note in `docs/FEATURES.md` or development docs for `/print`. |
| **Tests** | `tests/test_conversation_printer.py` extended; may refactor large HTML assertions into helpers. |

## Non-goals (this change)

- Replacing WeasyPrint with headless Chrome/Puppeteer or a full LaTeX toolchain.
- Pixel-perfect match to any external product; goal is **professional, consistent** FinOps Buddy output comparable to **`markdown-to-pdf-guide.md`** and the **cost-anomaly-report** sample.
- Changing **txt/csv/xlsx** export layout beyond what is needed for shared Markdown normalization.

## References (in-repo)

- **`markdown-to-pdf-guide.md`** — canonical pipeline and CSS design rationale.
- **`cost-anomaly-report-2026-03-27.md`** — example Markdown structure and table density to aim for.
- **`cost-anomaly-report-2026-03-27.pdf`** — visual quality bar (if available in the workspace for designers/reviewers).
- Archived proposal: **`openspec/changes/archive/2026-03-11-conversation-printer/proposal.md`** — original `/print` scope.
