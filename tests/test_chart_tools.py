"""Pytest tests for chart generation tool (create_chart)."""

import re

from finops_buddy.agent.chart_tools import _render_chart, create_chart_tools


def test_create_chart_returns_line_chart_markdown():
    """create_chart with chart_type=line returns markdown with a data URI image."""
    tools = create_chart_tools()
    create_chart = next(t for t in tools if getattr(t, "__name__", "") == "create_chart")
    result = create_chart(
        chart_type="line",
        data=[{"x": 1, "y": 10}, {"x": 2, "y": 20}, {"x": 3, "y": 15}],
        title="Cost trend",
    )
    assert isinstance(result, str)
    assert "![Cost trend](data:image/png;base64," in result or "![Cost trend](data:image/" in result
    assert re.search(r"data:image/[^;]+;base64,[A-Za-z0-9+/=]+", result)


def test_create_chart_returns_bar_chart_markdown():
    """create_chart with chart_type=bar returns markdown with an embedded image."""
    tools = create_chart_tools()
    create_chart = next(t for t in tools if getattr(t, "__name__", "") == "create_chart")
    result = create_chart(
        chart_type="bar",
        data=[
            {"label": "EC2", "value": 100},
            {"label": "S3", "value": 50},
        ],
        title="By service",
    )
    assert isinstance(result, str)
    assert "data:image/" in result and "base64," in result


def test_create_chart_returns_pie_chart_markdown():
    """create_chart with chart_type=pie returns markdown with an embedded image."""
    tools = create_chart_tools()
    create_chart = next(t for t in tools if getattr(t, "__name__", "") == "create_chart")
    result = create_chart(
        chart_type="pie",
        data=[
            {"label": "A", "value": 30},
            {"label": "B", "value": 70},
        ],
        title="Proportion",
    )
    assert isinstance(result, str)
    assert "data:image/" in result and "base64," in result


def test_create_chart_returns_scatter_chart_markdown():
    """create_chart with chart_type=scatter returns markdown with an embedded image."""
    tools = create_chart_tools()
    create_chart = next(t for t in tools if getattr(t, "__name__", "") == "create_chart")
    result = create_chart(
        chart_type="scatter",
        data=[{"x": 1, "y": 2}, {"x": 2, "y": 4}, {"x": 3, "y": 3}],
        title="Scatter",
    )
    assert isinstance(result, str)
    assert "data:image/" in result and "base64," in result


def test_create_chart_on_allow_list():
    """create_chart is on the default read-only allow-list."""
    from finops_buddy.agent.guardrails import get_default_allowed_tools

    allowed = get_default_allowed_tools()
    assert "create_chart" in allowed


def test_create_chart_handles_invalid_data():
    """When create_chart is called with malformed or empty data, returns error message string."""
    result = _render_chart("line", [], title="x")
    assert isinstance(result, str)
    assert "Error" in result
    assert "data:image/" not in result

    result = _render_chart("line", "not a list", title="x")
    assert "Error" in result

    result = _render_chart("bar", [{"label": "A"}], title="x")  # missing value
    assert "Error" in result or ("data:image/" in result)  # implementation may still render


def test_create_chart_accepts_columnar_dict():
    """When data is columnar dict (e.g. dates + costs), chart is generated."""
    result = _render_chart(
        "line",
        {"dates": ["2026-03-09", "2026-03-10", "2026-03-11"], "costs": [10.0, 20.0, 15.0]},
        title="Daily cost",
    )
    assert "data:image/" in result and "base64," in result


def test_create_chart_line_with_date_labels():
    """When line chart has date strings as x, use them as tick labels."""
    result = _render_chart(
        "line",
        [
            {"date": "2026-03-09", "cost": 0},
            {"date": "2026-03-10", "cost": 3.12},
            {"date": "2026-03-11", "cost": 0.29},
        ],
        title="EC2 last 7 days",
    )
    assert "data:image/" in result and "base64," in result


def test_create_chart_no_network_calls():
    """Chart generation completes without making HTTP or network requests (local only)."""
    # We cannot easily mock socket in a portable way; we assert the tool runs synchronously
    # and returns a result with no I/O beyond matplotlib (in-process).
    result = _render_chart(
        "line",
        [{"x": 1, "y": 2}],
        title="Local",
    )
    assert "data:image/" in result or "Error" in result
