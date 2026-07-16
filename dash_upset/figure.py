"""Render an :class:`~dash_upset.data.UpSetData` model as a Plotly figure.

The figure is composed from Plotly primitives on a 2x2 subplot grid:

- top right: intersection-size bars,
- bottom left: set-size bars (growing leftward),
- bottom right: the membership dot matrix with connector lines.

The three panels share axes, so zooming and panning stay consistent. Every
trace carries a stable ``meta`` identifier (``"upset:intersection-bars"``,
``"upset:set-bars"``, ``"upset:matrix-background"``, ``"upset:matrix-dots"``,
``"upset:matrix-connectors"``) so downstream code (and the M2 Dash component)
can address them without relying on trace order.
"""

from __future__ import annotations

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .data import UpSetData, UpSetIntersection, sort_intersections, sort_sets, subset_sizes

__all__ = ["create_upset"]

# Neutral ink ramp: near-black data marks, quiet chrome (see ROADMAP theming
# notes; a template-aware light/dark story lands in M3).
_INK = "#0b0b0b"
_SECONDARY_INK = "#52514e"
_MUTED_INK = "#898781"
_INACTIVE = "#d8d7d1"
_GRID = "#e1e0d9"
_BASELINE = "#c3c2b7"
_BAND = "rgba(11, 11, 11, 0.04)"

_ROW_PX = 28
_BAR_PANEL_PX = 300


def _label(intersection: UpSetIntersection) -> str:
    return " & ".join(intersection.sets) if intersection.sets else "(no sets)"


def _percent(part: float, total: float) -> str:
    return f"{100 * part / total:.1f}" if total > 0 else "0.0"


def create_upset(
    data: UpSetData,
    *,
    mode: str = "distinct",
    sort_by: str = "cardinality",
    sort_sets_by: str = "cardinality",
    show_empty: bool = False,
    show_counts: bool = True,
    color: str = _INK,
    inactive_color: str = _INACTIVE,
    title: str | None = None,
    width: int | None = None,
    height: int | None = None,
    template: str | None = "plotly_white",
) -> go.Figure:
    """Create an UpSet plot as a standalone Plotly figure.

    Args:
        data: The canonical model, built with one of the ``from_*``
            constructors in :mod:`dash_upset.data`.
        mode: How subset sizes are counted: ``"distinct"`` (default, exclusive
            intersections that partition the data), ``"intersect"`` (inclusive:
            elements in all member sets), or ``"union"`` (elements in at least
            one member set). See :func:`dash_upset.data.subset_sizes`. In the
            two overlapping modes the bars no longer sum to the total.
        sort_by: Intersection order: ``"cardinality"`` (largest first),
            ``"degree"``, or ``"input"``; prefix with ``-`` to reverse.
        sort_sets_by: Set order: ``"cardinality"``, ``"name"``, or
            ``"input"``; prefix with ``-`` to reverse.
        show_empty: Include the degree-0 intersection (elements in no set).
        show_counts: Label each intersection bar with its size.
        color: Color of the data marks (bars, active dots, connectors).
        inactive_color: Color of the non-member matrix dots.
        title: Optional figure title.
        width: Figure width in pixels; ``None`` means responsive.
        height: Figure height in pixels; ``None`` computes one from the
            number of sets.
        template: Plotly template; ``None`` inherits the global default.

    Returns:
        A :class:`plotly.graph_objects.Figure`, ready for ``fig.show()``,
        ``dcc.Graph(figure=fig)``, or static export.
    """
    if not isinstance(data, UpSetData):
        raise TypeError(
            "create_upset expects an UpSetData model; build one with "
            "from_memberships, from_contents, from_indicators, or from_counts "
            f"(got {type(data).__name__})"
        )
    if not data.set_names:
        raise ValueError("the data model has no sets to plot")
    if not data.intersections:
        raise ValueError("the data model has no intersections to plot")

    shown = [entry for entry in subset_sizes(data, mode) if show_empty or entry.degree > 0]
    if not shown:
        raise ValueError(
            "all intersections have degree 0 (elements in no set); pass "
            "show_empty=True to display them"
        )

    set_order = sort_sets(data.set_names, data.set_sizes, sort_sets_by)
    intersections = sort_intersections(shown, set_order, sort_by)
    size_of_set = dict(zip(data.set_names, data.set_sizes, strict=True))
    row_of_set = {name: row for row, name in enumerate(set_order)}
    n_sets = len(set_order)
    n_intersections = len(intersections)
    total = data.total_size

    matrix_px = _ROW_PX * n_sets
    matrix_fraction = min(0.8, max(0.12, matrix_px / (matrix_px + _BAR_PANEL_PX)))
    chrome_px = 110 if title else 80
    if height is None:
        height = int(matrix_px + _BAR_PANEL_PX + chrome_px)
        row_px = float(_ROW_PX)
    else:
        row_px = max(1.0, (height - chrome_px) * matrix_fraction / n_sets)
    dot_px = min(16, max(8, round(row_px * 0.42)))
    connector_px = max(2.0, round(dot_px * 0.22, 1))

    fig = make_subplots(
        rows=2,
        cols=2,
        specs=[[None, {}], [{}, {}]],
        shared_xaxes=True,
        shared_yaxes=True,
        column_widths=[0.25, 0.75],
        row_heights=[1 - matrix_fraction, matrix_fraction],
        horizontal_spacing=0.02,
        vertical_spacing=0.04,
    )

    labels = [_label(entry) for entry in intersections]
    sizes = [entry.size for entry in intersections]
    fig.add_trace(
        go.Bar(
            x=list(range(n_intersections)),
            y=sizes,
            width=0.6,
            marker={"color": color, "cornerradius": 4, "line": {"width": 0}},
            customdata=[
                [label, entry.degree, _percent(entry.size, total)]
                for label, entry in zip(labels, intersections, strict=True)
            ],
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Size: %{y:,} (%{customdata[2]}% of total)<br>"
                "Degree: %{customdata[1]}<extra></extra>"
            ),
            texttemplate="%{y:,}" if show_counts else None,
            textposition="outside",
            textfont={"size": 11, "color": _SECONDARY_INK},
            cliponaxis=False,
            name="Intersection size",
            meta="upset:intersection-bars",
        ),
        row=1,
        col=2,
    )

    fig.add_trace(
        go.Bar(
            x=[size_of_set[name] for name in set_order],
            y=list(range(n_sets)),
            orientation="h",
            width=0.6,
            marker={"color": color, "cornerradius": 4, "line": {"width": 0}},
            customdata=[[name, _percent(size_of_set[name], total)] for name in set_order],
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Size: %{x:,} (%{customdata[1]}% of total)<extra></extra>"
            ),
            name="Set size",
            meta="upset:set-bars",
        ),
        row=2,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=[column for column in range(n_intersections) for _row in range(n_sets)],
            y=[row for _column in range(n_intersections) for row in range(n_sets)],
            mode="markers",
            marker={"color": inactive_color, "size": dot_px},
            hoverinfo="skip",
            name="Non-members",
            meta="upset:matrix-background",
        ),
        row=2,
        col=2,
    )

    connector_x: list[float | None] = []
    connector_y: list[float | None] = []
    for column, entry in enumerate(intersections):
        if entry.degree < 2:
            continue
        rows = [row_of_set[name] for name in entry.sets]
        connector_x += [column, column, None]
        connector_y += [min(rows), max(rows), None]
    if connector_x:
        fig.add_trace(
            go.Scatter(
                x=connector_x,
                y=connector_y,
                mode="lines",
                line={"color": color, "width": connector_px},
                hoverinfo="skip",
                name="Connectors",
                meta="upset:matrix-connectors",
            ),
            row=2,
            col=2,
        )

    dot_x: list[int] = []
    dot_y: list[int] = []
    dot_customdata: list[list[str]] = []
    for column, (label, entry) in enumerate(zip(labels, intersections, strict=True)):
        for name in entry.sets:
            dot_x.append(column)
            dot_y.append(row_of_set[name])
            dot_customdata.append([name, f"{label} ({entry.size:,})"])
    if dot_x:
        fig.add_trace(
            go.Scatter(
                x=dot_x,
                y=dot_y,
                mode="markers",
                marker={"color": color, "size": dot_px},
                customdata=dot_customdata,
                hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]}<extra></extra>",
                name="Members",
                meta="upset:matrix-dots",
            ),
            row=2,
            col=2,
        )

    matrix = fig.get_subplot(2, 2)
    matrix_x = matrix.yaxis.anchor or "x"
    matrix_y = matrix.xaxis.anchor or "y"
    for row in range(0, n_sets, 2):
        fig.add_shape(
            type="rect",
            xref=f"{matrix_x} domain",
            yref=matrix_y,
            x0=0,
            x1=1,
            y0=row - 0.5,
            y1=row + 0.5,
            fillcolor=_BAND,
            line={"width": 0},
            layer="below",
        )

    max_size = max(sizes)
    headroom = 1.18 if show_counts else 1.05
    intersection_range = [0, max_size * headroom if max_size > 0 else 1]
    column_range = [-0.5, n_intersections - 0.5]
    row_range = [n_sets - 0.5, -0.5]
    tick_font = {"size": 11, "color": _MUTED_INK}
    title_font = {"size": 12, "color": _SECONDARY_INK}
    intersection_title = {
        "distinct": "Intersection size",
        "intersect": "Intersection size (intersect)",
        "union": "Union size",
    }[mode]

    fig.update_xaxes(
        row=1,
        col=2,
        range=column_range,
        showticklabels=False,
        ticks="",
        showgrid=False,
        zeroline=False,
    )
    fig.update_yaxes(
        row=1,
        col=2,
        range=intersection_range,
        title_text=intersection_title,
        title_font=title_font,
        tickfont=tick_font,
        gridcolor=_GRID,
        gridwidth=1,
        zeroline=True,
        zerolinecolor=_BASELINE,
        zerolinewidth=1,
        nticks=5,
        automargin=True,
    )
    fig.update_xaxes(
        row=2,
        col=1,
        autorange="reversed",
        title_text="Set size",
        title_font=title_font,
        tickfont=tick_font,
        gridcolor=_GRID,
        gridwidth=1,
        zeroline=False,
        nticks=4,
        automargin=True,
    )
    fig.update_yaxes(
        row=2,
        col=1,
        range=row_range,
        tickvals=list(range(n_sets)),
        ticktext=list(set_order),
        tickfont={"size": 12, "color": _SECONDARY_INK},
        ticks="",
        showgrid=False,
        zeroline=False,
        automargin=True,
    )
    fig.update_xaxes(
        row=2,
        col=2,
        range=column_range,
        showticklabels=False,
        ticks="",
        showgrid=False,
        zeroline=False,
    )
    fig.update_yaxes(
        row=2,
        col=2,
        range=row_range,
        showticklabels=False,
        ticks="",
        showgrid=False,
        zeroline=False,
    )

    fig.update_layout(
        showlegend=False,
        width=width,
        height=height,
        margin={"l": 12, "r": 16, "t": 64 if title else 28, "b": 12},
        font={"size": 12, "color": _SECONDARY_INK},
        hoverlabel={"font": {"size": 12}},
    )
    if template is not None:
        fig.update_layout(template=template)
    if title is not None:
        fig.update_layout(
            title={"text": title, "x": 0, "xanchor": "left", "font": {"size": 15, "color": _INK}}
        )
    return fig
