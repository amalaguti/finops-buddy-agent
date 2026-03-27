## Context

FinOps Buddy exposes **`/print`** in the CLI chat loop (`src/finops_buddy/agent/chat_loop.py`), implemented by `run_print_flow` and `src/finops_buddy/agent/conversation_printer.py`. Users can export the session as **txt, pdf, csv, xlsx**. PDF generation today uses a **fallback chain**: WeasyPrint → xhtml2pdf → reportlab, then **PDF MCP** (`convert_markdown_to_pdf`) if all fallbacks fail.

The **proposal** and **`markdown-to-pdf-guide.md`** define a target pipeline: **Markdown → HTML (with `tables`) → full HTML document with embedded print CSS → WeasyPrint**. Current WeasyPrint code renders **unstyled** fragments (`<body>{html}</body>` only). xhtml2pdf uses a **minimal** stylesheet. **Markdown** uses `extra` + `nl2br` without prioritizing **`tables`**; **`nl2br`** can amplify vertical gaps when conversation text already contains blank lines.

There is **no** `openspec/specs/conversation-printer/spec.md` on main yet; the canonical text lives under **`openspec/changes/archive/2026-03-11-conversation-printer/specs/conversation-printer/spec.md`**. This change adds a delta spec to merge on apply.

## Goals / Non-Goals

**Goals:**

- **One presentation layer** for in-process PDF: shared **HTML document shell** + **default print CSS** (A4 `@page`, typography, table styling aligned with `markdown-to-pdf-guide.md` / FinOps-friendly palette).
- **Correct pipe tables** in PDF when agent/user content includes GFM-style tables: enable **`tables`** (and keep **`fenced_code`**, **`extra`** subsets as needed without duplicating breaks).
- **Tighter vertical rhythm**: normalize or constrain **excessive blank lines** before Markdown conversion; avoid **`nl2br`** unless required for fidelity (or apply only to specific patterns).
- **Same HTML+CSS input** to WeasyPrint and xhtml2pdf where CSS support allows; document **degradation** (e.g. `nth-child` on xhtml2pdf).
- **Predictable MCP behavior**: if in-process PDF succeeds with styled output, **do not** replace with MCP for “prettier” randomness; MCP used when in-process fails—**MCP receives markdown** today; if tool cannot take pre-styled HTML, **document** that MCP output may differ; optional follow-up to pass HTML only if API supports it.
- **Optional PDF header block**: title (e.g. “FinOps Buddy — conversation export”), **UTC/local timestamp**, optional **AWS profile name** when available from chat session context—no fabricated data.
- **Tests** that assert HTML contains stylesheet markers, table structure for pipe markdown, and no runaway whitespace for representative conversation strings.

**Non-Goals:**

- Headless Chrome, LaTeX, or pixel-perfect match to external tools.
- Redesigning **txt/csv/xlsx** beyond sharing **Markdown normalization** used for PDF input.
- Web UI **`/print`** (out of scope for this change unless already unified with same module later).

## Decisions

### D1 — Single helper: Markdown → styled HTML string

**Decision:** Introduce something like **`markdown_to_styled_html(markdown: str) -> str`** (name TBD) that:

1. Optionally **normalizes** input (collapse 3+ newlines to 2, trim trailing spaces on lines—exact rules in implementation).
2. Runs **`markdown.markdown(..., extensions=[...])`** with at least **`tables`**, **`fenced_code`**; **`nl2br`** off by default or narrowly scoped.
3. Wraps fragment in `<!DOCTYPE html>…<head><style>…</style></head><body>…</body></html>` using a **module-level CSS string** (or loaded from a single template file if size warrants).

**Rationale:** One code path feeds WeasyPrint and xhtml2pdf; avoids drift between “bare body” and “full doc.”

**Alternatives considered:** Separate CSS per backend (rejected: duplication); external `.css` file on disk (acceptable later for customization; default stays embedded for zero-config).

### D2 — Default stylesheet content

**Decision:** Base defaults on **`markdown-to-pdf-guide.md`** (A4 margins, body ~11px, tables ~10px, dark `th`, zebra `tr:nth-child(even)`, heading borders, `line-height` ~1.5, compact `p`/`h2` margins). Use **AWS-adjacent** neutrals (`#232f3e`, `#ff9900` accent) as in the guide unless product prefers theme tokens later.

**Rationale:** Matches user-provided quality bar and existing doc.

**Alternatives:** Minimal gray tables only (rejected: current pain point).

### D3 — Fallback order unchanged; behavior clarified

**Decision:** Keep **WeasyPrint → xhtml2pdf → reportlab → MCP**. **WeasyPrint** and **xhtml2pdf** both receive the **same styled HTML** from D1. **ReportLab** remains a **last in-process** fallback with **improved** `TableStyle` (header fill, grid, font sizes) aligned with palette constants—still **not** full Markdown parity.

**Rationale:** Preserves Windows-friendly path (xhtml2pdf) and existing MCP JSON-RPC stability (fallback-first avoids MCP stdout pollution).

**Alternatives:** MCP-first for quality (rejected: unpredictable styling, prior channel issues).

### D4 — MCP input

**Decision:** Continue passing **markdown** to **`convert_markdown_to_pdf`** unless we verify the MCP accepts HTML/CSS; **do not** block release on MCP styling parity—**in-process** path is the **reference** for “professional” output.

**Rationale:** Proposal asks for predictable quality; MCP is escape hatch.

### D5 — Optional env for custom CSS (defer to tasks if low value)

**Decision:** **Optional** `FINOPS_PRINT_PDF_CSS_PATH` or `agent.print_pdf_css_path` in settings pointing to a user `.css` file **merged or replaced** with defaults—**only if** implementation stays small; otherwise defer to a follow-up change.

**Rationale:** Keeps first iteration focused; proposal listed optional config.

### D6 — Agent `export_to_pdf` tools

**Decision:** If **`create_export_tools`** builds PDF via the same `export_pdf` path, **no separate code path**—styled pipeline benefits both `/print` and tool calls automatically. Verify in tasks.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| **xhtml2pdf** weak CSS (no `nth-child`, flex) | Document degradation; keep zebra via **manual row classes** only if worth complexity; else accept flat rows on xhtml2pdf. |
| **WeasyPrint** missing on Windows | Already mitigated by xhtml2pdf/reportlab; ensure styled HTML works on xhtml2pdf. |
| **Normalization** breaks user intent (preserving many blank lines) | Conservative rules (collapse only **excessive** runs); optional spec scenario for “preserves intentional paragraph break = double newline”. |
| **Larger HTML string** in memory | Negligible for chat-sized exports. |
| **MCP PDF** looks different from in-process | Document in CONFIGURATION; in-process is quality reference. |

## Migration Plan

- **Deploy:** Standard app update; no data migration.
- **Rollback:** Revert commit restoring previous `conversation_printer` helpers.
- **Users:** No settings change required; optional CSS path is additive.

## Open Questions

- Does **md-to-pdf-mcp** accept HTML or theme parameters? (Spike during implementation; optional doc note.)
- Should **PDF header** include **account id** when profile is resolved? (Only if already in session context without extra AWS calls.)
