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

from .data import (
    UpSetData,
    UpSetIntersection,
    deviations,
    filter_subsets,
    sort_intersections,
    sort_sets,
    subset_sizes,
)

__all__ = ["create_upset"]

# Theme chrome: light and dark bases (near-black marks on white / near-white
# marks on ink), plus CVD-safe qualitative palettes for the colorway. An
# explicit ``color`` / ``inactive_color`` always wins over the theme.
_LIGHT = {
    "ink": "#0b0b0b",
    "paper": "#ffffff",
    "secondary": "#52514e",
    "muted": "#898781",
    "inactive": "#d8d7d1",
    "grid": "#e1e0d9",
    "baseline": "#c3c2b7",
    "band": "rgba(11, 11, 11, 0.04)",
}
_DARK = {
    "ink": "#e8e6e1",
    "paper": "#1a1a19",
    "secondary": "#c3c2b7",
    "muted": "#8f8d86",
    "inactive": "#3d3d3a",
    "grid": "#2c2c2a",
    "baseline": "#45443e",
    "band": "rgba(255, 255, 255, 0.05)",
}
# (light colorway, dark colorway) per palette. Okabe-Ito and Paul Tol read on
# either surface; ColorBrewer uses Set2 (light) / Dark2 (dark).
_OKABE_ITO = ["#E69F00", "#56B4E9", "#009E73", "#F0E442", "#0072B2", "#D55E00", "#CC79A7"]
_PALETTES = {
    "okabe-ito": (_OKABE_ITO, _OKABE_ITO),
    "colorbrewer": (
        ["#66C2A5", "#FC8D62", "#8DA0CB", "#E78AC3", "#A6D854", "#FFD92F", "#E5C494"],
        ["#1B9E77", "#D95F02", "#7570B3", "#E7298A", "#66A61E", "#E6AB02", "#A6761D"],
    ),
    "tol": (
        ["#4477AA", "#EE6677", "#228833", "#CCBB44", "#66CCEE", "#AA3377", "#BBBBBB"],
        ["#4477AA", "#EE6677", "#228833", "#CCBB44", "#66CCEE", "#AA3377", "#BBBBBB"],
    ),
}
THEMES = (
    "light",
    "dark",
    "auto",
    "okabe-ito-light",
    "okabe-ito-dark",
    "colorbrewer-light",
    "colorbrewer-dark",
    "tol-light",
    "tol-dark",
)

_ROW_PX = 28
_BAR_PANEL_PX = 300


def _label(intersection: UpSetIntersection) -> str:
    return " & ".join(intersection.sets) if intersection.sets else "(no sets)"


def _percent(part: float, total: float) -> str:
    return f"{100 * part / total:.1f}" if total > 0 else "0.0"


def _resolve_theme(theme: str) -> dict:
    """Resolve a ``theme`` name to a chrome dict + colorway.

    Mirrors the dash-seqviz theme vocabulary: ``"light"`` (default),
    ``"dark"``, ``"auto"``, and CVD-safe ``"{okabe-ito,colorbrewer,tol}-{light,
    dark}"``. A static figure cannot read the page's color scheme, so
    ``"auto"`` resolves to ``"light"`` here; the interactive Dash component
    makes it live (following ``data-mantine-color-scheme`` / the OS setting).
    """
    name = "light" if theme == "auto" else theme
    for palette, (light_cw, dark_cw) in _PALETTES.items():
        if name in (palette, f"{palette}-light"):
            return {**_LIGHT, "colorway": light_cw}
        if name == f"{palette}-dark":
            return {**_DARK, "colorway": dark_cw}
    if name == "light":
        return {**_LIGHT, "colorway": None}
    if name == "dark":
        return {**_DARK, "colorway": None}
    options = ", ".join(repr(option) for option in THEMES)
    raise ValueError(f"theme must be one of {options}, got {theme!r}")


def create_upset(
    data: UpSetData,
    *,
    mode: str = "distinct",
    sort_by: str = "cardinality",
    sort_sets_by: str = "cardinality",
    min_subset_size: float | None = None,
    max_subset_size: float | None = None,
    min_degree: int | None = None,
    max_degree: int | None = None,
    max_subsets: int | None = None,
    show_empty: bool = False,
    show_counts: bool = True,
    show_percentages: bool = False,
    theme: str = "light",
    color: str | None = None,
    inactive_color: str | None = None,
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
        min_subset_size: Drop subsets smaller than this (inclusive bound on the
            mode-dependent size).
        max_subset_size: Drop subsets larger than this.
        min_degree: Drop subsets with fewer than this many participating sets.
        max_degree: Drop subsets with more than this many participating sets.
        max_subsets: Keep only the N largest subsets by size (ties at the
            cutoff are all kept).
        show_empty: Include the degree-0 intersection (elements in no set).
        show_counts: Label each intersection bar with its size.
        show_percentages: Label each intersection bar with its percentage of
            the total. Combined with ``show_counts`` the label reads
            ``"N (X%)"``; alone it reads ``"X%"``.
        theme: Visual theme. ``"light"`` (default), ``"dark"``, or ``"auto"``,
            plus CVD-safe palette variants ``"okabe-ito-light"`` /
            ``"okabe-ito-dark"``, ``"colorbrewer-light"`` /
            ``"colorbrewer-dark"``, ``"tol-light"`` / ``"tol-dark"``. Light and
            dark recolor the marks and chrome for the background; the palette
            variants also set a colorblind-safe colorway. ``"auto"`` resolves to
            light for a static figure (the Dash component makes it follow the
            page live).
        color: Color of the data marks (bars, active dots, connectors).
            Defaults to the theme's ink; an explicit value overrides the theme.
        inactive_color: Color of the non-member matrix dots. Defaults to the
            theme's inactive tone; an explicit value overrides the theme.
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
    shown = list(
        filter_subsets(
            shown,
            min_size=min_subset_size,
            max_size=max_subset_size,
            min_degree=min_degree,
            max_degree=max_degree,
            max_subsets=max_subsets,
        )
    )
    if not shown:
        raise ValueError("no subsets remain after filtering; loosen the filter parameters")

    set_order = sort_sets(data.set_names, data.set_sizes, sort_sets_by)
    deviation_map = deviations(data)
    intersections = sort_intersections(shown, set_order, sort_by, deviation_map=deviation_map)
    size_of_set = dict(zip(data.set_names, data.set_sizes, strict=True))
    row_of_set = {name: row for row, name in enumerate(set_order)}
    n_sets = len(set_order)
    n_intersections = len(intersections)
    total = data.total_size

    th = _resolve_theme(theme)
    ink = color if color is not None else th["ink"]
    inactive = inactive_color if inactive_color is not None else th["inactive"]

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
    if show_counts and show_percentages:
        bar_text = "%{y:,} (%{customdata[2]}%)"
    elif show_counts:
        bar_text = "%{y:,}"
    elif show_percentages:
        bar_text = "%{customdata[2]}%"
    else:
        bar_text = None
    fig.add_trace(
        go.Bar(
            x=list(range(n_intersections)),
            y=sizes,
            width=0.6,
            marker={"color": ink, "cornerradius": 4, "line": {"width": 0}},
            customdata=[
                [
                    label,
                    entry.degree,
                    _percent(entry.size, total),
                    f"{100 * deviation_map[frozenset(entry.sets)]:+.1f}",
                ]
                for label, entry in zip(labels, intersections, strict=True)
            ],
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Size: %{y:,} (%{customdata[2]}% of total)<br>"
                "Degree: %{customdata[1]}<br>"
                "Deviation: %{customdata[3]}%<extra></extra>"
            ),
            texttemplate=bar_text,
            textposition="outside",
            textfont={"size": 11, "color": th["secondary"]},
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
            marker={"color": ink, "cornerradius": 4, "line": {"width": 0}},
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
            marker={"color": inactive, "size": dot_px},
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
                line={"color": ink, "width": connector_px},
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
                marker={"color": ink, "size": dot_px},
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
            fillcolor=th["band"],
            line={"width": 0},
            layer="below",
        )

    max_size = max(sizes)
    headroom = 1.18 if (show_counts or show_percentages) else 1.05
    intersection_range = [0, max_size * headroom if max_size > 0 else 1]
    column_range = [-0.5, n_intersections - 0.5]
    row_range = [n_sets - 0.5, -0.5]
    tick_font = {"size": 11, "color": th["muted"]}
    title_font = {"size": 12, "color": th["secondary"]}
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
        gridcolor=th["grid"],
        gridwidth=1,
        zeroline=True,
        zerolinecolor=th["baseline"],
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
        gridcolor=th["grid"],
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
        tickfont={"size": 12, "color": th["secondary"]},
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
        font={"size": 12, "color": th["secondary"]},
        paper_bgcolor=th["paper"],
        plot_bgcolor=th["paper"],
        colorway=th["colorway"],
        hoverlabel={"font": {"size": 12}},
    )
    if template is not None:
        fig.update_layout(template=template)
    if title is not None:
        fig.update_layout(
            title={
                "text": title,
                "x": 0,
                "xanchor": "left",
                "font": {"size": 15, "color": th["ink"]},
            }
        )
    return fig
