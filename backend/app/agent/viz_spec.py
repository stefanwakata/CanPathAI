"""Plotly figure-spec builder. Pure logic (dict output) — unit-testable.

The agent's Visualization tool passes rows + a chart request; we emit a
Plotly JSON spec the React frontend renders with react-plotly.js. Building
dicts (not plotly Figure objects) keeps this dependency-free and serializable.
"""
from typing import Any

VALID_KINDS = {"bar", "line", "grouped_bar", "pie"}

_LAYOUT_BASE: dict[str, Any] = {
    "template": "plotly_white",
    "margin": {"l": 60, "r": 20, "t": 50, "b": 60},
    "height": 380,
    "font": {"family": "Inter, system-ui, sans-serif", "size": 13},
    "colorway": ["#b23a48", "#1f6f8b", "#e08e45", "#4a7c59", "#7d5ba6", "#c98bb9"],
}


def build_figure(
    kind: str,
    rows: list[dict[str, Any]],
    *,
    x: str,
    y: str,
    series: str | None = None,
    title: str = "",
) -> dict[str, Any]:
    """Build a Plotly figure dict from tabular rows.

    kind: bar | line | grouped_bar | pie
    x/y: column names in rows; series: optional grouping column.
    """
    if kind not in VALID_KINDS:
        raise ValueError(f"Unsupported chart kind '{kind}'. Use one of {sorted(VALID_KINDS)}")
    if not rows:
        raise ValueError("No rows to plot")
    for col in filter(None, [x, y, series]):
        if col not in rows[0]:
            raise ValueError(f"Column '{col}' not in rows (have: {list(rows[0])})")

    layout = {**_LAYOUT_BASE, "title": {"text": title}}
    if kind == "pie":
        data = [{
            "type": "pie",
            "labels": [r[x] for r in rows],
            "values": [r[y] for r in rows],
            "hole": 0.35,
        }]
        return {"data": data, "layout": layout}

    trace_type = "scatter" if kind == "line" else "bar"
    extra = {"mode": "lines+markers"} if kind == "line" else {}

    if series:
        groups: dict[str, list[dict]] = {}
        for r in rows:
            groups.setdefault(str(r[series]), []).append(r)
        data = [
            {"type": trace_type, "name": name,
             "x": [r[x] for r in g], "y": [r[y] for r in g], **extra}
            for name, g in groups.items()
        ]
        if kind == "grouped_bar":
            layout["barmode"] = "group"
    else:
        data = [{"type": trace_type, "x": [r[x] for r in rows], "y": [r[y] for r in rows], **extra}]

    layout["xaxis"] = {"title": {"text": x}}
    layout["yaxis"] = {"title": {"text": y}}
    return {"data": data, "layout": layout}
