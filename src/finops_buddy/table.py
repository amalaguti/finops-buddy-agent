"""Format cost data as a terminal table."""

from __future__ import annotations

from decimal import Decimal


def format_costs_table(
    rows: list[tuple[str, Decimal]],
    *,
    include_pct: bool = True,
    currency: str = "USD",
) -> str:
    """
    Format (service_name, cost) rows as an aligned table.

    Columns: Service, Cost, and optionally % of total.
    """
    if not rows:
        return "No cost data for the period."
    total = sum(c for _, c in rows)
    # Column widths
    max_svc = max(len(s) for s, _ in rows)
    max_svc = max(max_svc, len("Service"))
    # Cost column: format as 12.34 (2 decimals)
    cost_width = 12
    pct_width = 6 if include_pct else 0
    lines = []
    header = f"{'Service':<{max_svc}}  {'Cost':>{cost_width}}"
    if include_pct:
        header += f"  {'%':>{pct_width}}"
    lines.append(header)
    lines.append("-" * (max_svc + 2 + cost_width + (2 + pct_width if include_pct else 0)))
    for svc, cost in rows:
        cost_str = f"{float(cost):,.2f}"
        row = f"{svc:<{max_svc}}  {cost_str:>{cost_width}}"
        if include_pct and total > 0:
            pct = float(cost) / float(total) * 100
            row += f"  {pct:>{pct_width}.1f}%"
        lines.append(row)
    if include_pct and total > 0:
        lines.append("-" * len(lines[-1]))
        lines.append(f"{'Total':<{max_svc}}  {float(total):>{cost_width},.2f}  100.0%")
    return "\n".join(lines)
