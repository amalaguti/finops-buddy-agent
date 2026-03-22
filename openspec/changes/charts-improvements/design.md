## Context

`create_chart` in `chart_tools.py` uses `matplotlib` with backend `Agg`, builds a figure with `plt.subplots()`, and saves PNG to a buffer at **100 DPI** with `fig.tight_layout()` only. No stylesheet is applied; bar charts use row order as given. The UI and API expect **markdown with `data:image/png;base64,...`** unchanged.

## Goals / Non-Goals

**Goals:**

- Nicer, more consistent **visual defaults** (grid, typography, color cycle) via a **single place** in `chart_tools` applied on every render.
- **Sharper, better-framed** PNGs for inline chat (DPI, figure size, `savefig` bbox/padding).
- **Descending bar order** for readability on cost breakdowns without asking the model to pre-sort.

**Non-Goals:**

- Plotly, Seaborn, Altair, SVG, or interactive charts.
- Changing the `create_chart` tool signature or response format.
- User-facing YAML settings or new **required** `FINOPS_*` variables (optional env overrides deferred unless product asks).
- Perfect pixel-identical output across OS/font installs (headless servers may fall back to bundled fonts).

## Decisions

1. **Styling mechanism:** Call `matplotlib.style.use(...)` with a **built-in** stylesheet (e.g. `seaborn-v0_8-whitegrid` or `tableau-colorblind10`) **inside** `_render_chart` after `matplotlib.use("Agg")`, then apply a small set of **`rcParams`** overrides for DPI, `figure.figsize`, and `savefig` options. **Rationale:** No new dependency; predictable in CI; easy to swap stylesheet name in one constant.

2. **DPI and figure size:** Raise default **save DPI** to **~150–160** (exact value chosen in implementation) and set **`figure.figsize`** to something like **8×4.5 inches** (or similar) so inline images are legible without huge payloads. **Rationale:** Chat panes are wide enough; doubling resolution from 100 DPI is a clear win; file size remains acceptable for base64 in responses.

3. **Save margins:** Use `savefig(..., bbox_inches="tight", pad_inches=...)` with a small positive pad so labels are not clipped. **Rationale:** Better use of canvas than `tight_layout()` alone in some cases; still compatible with `BytesIO`.

4. **Bar sort:** Before `ax.bar`, **zip labels and values**, sort by value descending, stable sort on ties (Python `sorted` with key and original index). **Rationale:** FinOps bar charts are almost always “top N”; line charts must keep time order; pie/scatter unchanged.

5. **Global state:** Matplotlib’s style/rc state is process-global. For this tool, **set style and overrides once per `_render_chart` call** (or via a context manager restoring previous rc if we want isolation). **Rationale:** Avoids cross-request leakage in long-lived workers; minimal code.

**Alternatives considered:**

- **Seaborn as dependency:** Rejected for this change to avoid extra package and audit surface; built-in matplotlib styles suffice.
- **Optional `FINOPS_CHART_DPI`:** Deferred; add in a later change if operators need tuning.
- **Currency formatting on axes:** Deferred; requires heuristics or new tool args; out of scope for “styling + render knobs” only.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Larger PNG payloads | Moderate DPI/figsize; monitor response size; compress only if needed later |
| Stylesheet name differs across matplotlib versions | Prefer stable names; pin minimum matplotlib in `pyproject.toml` if needed; fallback to `"default"` in code if `use()` fails (document in tasks) |
| Bar sort surprises a user who wanted input order | Scope is **bar only**; document in spec; rare for cost breakdowns |
| rcParams affect other code in same process | Scope imports inside `_render_chart`; consider `rc_context` to limit duration |

## Migration Plan

Deploy with application update only. No data migration. Rollback = revert `chart_tools.py` and tests.

## Open Questions

- Exact **stylesheet** name to standardize on (team preference: colorblind-safe vs. grid-heavy).
- Whether to add **`FINOPS_CHART_DPI`** in a fast follow-up for constrained environments.
