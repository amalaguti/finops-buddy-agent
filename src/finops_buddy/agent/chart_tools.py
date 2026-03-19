"""Chart generation tool for the Strands agent (matplotlib, local only)."""

from __future__ import annotations

import base64
import io
import json
from typing import Any


def _normalize_data(data: Any) -> list[dict[str, Any]] | None:
    """
    Normalize chart data to a list of dicts for consistent handling.

    Accepts:
    - list of dicts: [{"x": 1, "y": 2}, ...] or [{"label": "A", "value": 10}, ...]
    - columnar dict: {"x": [1,2,3], "y": [4,5,6]} or {"labels": [...], "values": [...]}
    - JSON string of either of the above
    """
    if data is None:
        return None
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except (json.JSONDecodeError, TypeError):
            return None
    if isinstance(data, list):
        if not data:
            return None
        # Ensure each item is a dict (skip non-dicts)
        out = []
        for item in data:
            if isinstance(item, dict):
                out.append(item)
            elif isinstance(item, (list, tuple)) and len(item) >= 2:
                # Allow [[x, y], ...] or [["label", "value"], ...]
                try:
                    out.append({"x": item[0], "y": item[1]})
                except (IndexError, TypeError):
                    pass
        return out if out else None
    if isinstance(data, dict):
        # Columnar: {"x": [...], "y": [...]} or {"labels": [...], "values": [...]}
        list_keys = [k for k in data if isinstance(data.get(k), list)]
        if len(list_keys) < 2:
            return None
        cols = [data[k] for k in list_keys]
        n = len(cols[0])
        if not n or not all(len(c) == n for c in cols):
            return None
        return [dict(zip(list_keys, row)) for row in zip(*cols)]
    return None


def _row_get(row: dict, keys: tuple[str, ...], case_insensitive: bool = True) -> Any | None:
    """Get value from row by key; case-insensitive, allow prefix (e.g. date matches dates)."""
    for k in keys:
        if k in row:
            return row[k]
        if case_insensitive and isinstance(row, dict):
            k_lower = k.lower()
            for rk, rv in row.items():
                if not isinstance(rk, str):
                    continue
                rk_lower = rk.lower()
                if rk_lower == k_lower or rk_lower.startswith(k_lower):
                    return rv
                if k_lower.startswith(rk_lower):
                    return rv
    return None


def _render_chart(
    chart_type: str,
    data: list[dict[str, Any]],
    title: str | None = None,
    x_label: str | None = None,
    y_label: str | None = None,
) -> str:
    """
    Generate a static chart from structured data and return markdown with embedded PNG.

    Args:
        chart_type: One of "line", "bar", "pie", "scatter".
        data: List of dicts. For line/scatter: [{"x": v, "y": v}, ...];
              for bar/pie: [{"label": s, "value": n}, ...]. Keys may vary (e.g. "name"/"amount").
        title: Optional chart title.
        x_label: Optional x-axis label (line, bar, scatter).
        y_label: Optional y-axis label (line, bar, scatter).

    Returns:
        Markdown string with embedded image: ![title](data:image/png;base64,...)
        or an error message string on invalid data.
    """
    data = _normalize_data(data)
    if not data:
        return (
            "Error: data must be a non-empty list of records (e.g. [{x, y}] or [{label, value}]), "
            'or a columnar dict (e.g. {"x": [1,2,3], "y": [4,5,6]}).'
        )

    chart_type = (chart_type or "").strip().lower()
    if chart_type not in ("line", "bar", "pie", "scatter"):
        return f"Error: chart_type must be one of: line, bar, pie, scatter. Got: {chart_type!r}."

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    try:
        buf = io.BytesIO()
        fig, ax = plt.subplots()

        if chart_type == "line":
            xs_num = _get_numeric_list(data, _NUMERIC_X_KEYS)
            ys = _get_numeric_list(data, _NUMERIC_Y_KEYS)
            x_labels = _get_value_list(data, _NUMERIC_X_KEYS)
            if not ys:
                return "Error: for line chart, data must have a numeric series (y/value/cost)."
            n = len(ys)
            if xs_num and len(xs_num) == n:
                xs = xs_num
                x_ticks = None
            elif x_labels and len(x_labels) == n:
                xs = list(range(n))
                x_ticks = x_labels
            else:
                xs = list(range(n))
                x_ticks = None
            ax.plot(xs, ys)
            if x_ticks is not None:
                ax.set_xticks(xs)
                ax.set_xticklabels(x_ticks, rotation=45, ha="right")
            if x_label:
                ax.set_xlabel(x_label)
            if y_label:
                ax.set_ylabel(y_label)

        elif chart_type == "bar":
            labels = _get_value_list(data, _LABEL_KEYS)
            values = _get_numeric_list(data, _NUMERIC_Y_KEYS)
            if not labels or not values or len(labels) != len(values):
                return "Error: for bar chart, data must have labels and values."
            ax.bar(labels, values)
            if x_label:
                ax.set_xlabel(x_label)
            if y_label:
                ax.set_ylabel(y_label)
            plt.xticks(rotation=45, ha="right")

        elif chart_type == "pie":
            labels = _get_value_list(data, _LABEL_KEYS)
            values = _get_numeric_list(data, _NUMERIC_Y_KEYS)
            if not labels or not values or len(labels) != len(values):
                return "Error: for pie chart, data must have labels and values."
            ax.pie(values, labels=labels, autopct="%1.1f%%", startangle=90)

        else:  # scatter
            xs = _get_numeric_list(data, _NUMERIC_X_KEYS)
            ys = _get_numeric_list(data, _NUMERIC_Y_KEYS)
            if not xs or not ys or len(xs) != len(ys):
                return "Error: for scatter chart, data must have matching x and y (e.g. [{x, y}])."
            ax.scatter(xs, ys)
            if x_label:
                ax.set_xlabel(x_label)
            if y_label:
                ax.set_ylabel(y_label)

        if title:
            ax.set_title(title)
        fig.tight_layout()
        fig.savefig(buf, format="png", dpi=100)
        plt.close(fig)
        buf.seek(0)
        b64 = base64.b64encode(buf.read()).decode("ascii")
        alt = title or "Chart"
        return f"![{alt}](data:image/png;base64,{b64})"
    except (ValueError, TypeError, KeyError) as e:
        return f"Error generating chart: {e}"
    except Exception as e:
        return f"Error generating chart: {e}"


# Key aliases for numeric series (order matters; first match wins).
_NUMERIC_X_KEYS = (
    "x",
    "date",
    "time",
    "label",
    "day",
    "period",
    "index",
    "date_str",
    "timestamp",
)
_NUMERIC_Y_KEYS = (
    "y",
    "value",
    "cost",
    "amount",
    "cost_usage",
    "amount_usd",
    "unblended_cost",
    "cost_usd",
)
_LABEL_KEYS = (
    "label",
    "name",
    "service",
    "account",
    "x",
    "category",
    "service_name",
    "account_name",
)


def _get_numeric_list(rows: list[dict], keys: tuple[str, ...]) -> list[float]:
    """Extract a list of numbers from rows; use _row_get for case-insensitive key match."""
    out = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        v = _row_get(row, keys)
        if v is None:
            for val in row.values():
                if isinstance(val, (int, float)):
                    out.append(float(val))
                    break
                if isinstance(val, str):
                    try:
                        out.append(float(val))
                        break
                    except ValueError:
                        pass
            continue
        if isinstance(v, (int, float)):
            out.append(float(v))
        elif isinstance(v, str):
            try:
                out.append(float(v))
            except ValueError:
                pass
    return out


def _get_value_list(rows: list[dict], keys: tuple[str, ...]) -> list[str]:
    """Extract a list of string values from rows; use _row_get for case-insensitive key match."""
    out = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        v = _row_get(row, keys)
        if v is not None:
            out.append(str(v))
        else:
            for val in row.values():
                out.append(str(val))
                break
    return out


def create_chart_tools() -> list:
    """
    Create Strands-compatible chart tools (no session required).
    Returns a list of tool functions to pass to Agent(tools=...).
    """
    from strands import tool

    @tool
    def create_chart(
        chart_type: str,
        data: list[dict] | dict,
        title: str | None = None,
        x_label: str | None = None,
        y_label: str | None = None,
    ) -> str:
        """
        Generate a chart image from cost or usage data. Call whenever the user asks for a
        chart, graph, or visual (e.g. bar chart of top 5 services). Do not substitute
        text or tables—call this tool so a chart image is embedded.
        chart_type: "line" (time series), "bar" (top N/categories), "pie", "scatter".
        data: List of dicts (label/value or date/cost) or columnar (labels/values). Keys flexible.
        """
        return _render_chart(
            chart_type=chart_type,
            data=data,
            title=title,
            x_label=x_label,
            y_label=y_label,
        )

    return [create_chart]
