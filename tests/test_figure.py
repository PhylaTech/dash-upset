"""Tests for the create_upset figure factory."""

import plotly.graph_objects as go
import pytest

from dash_upset import UpSetData, UpSetIntersection, create_upset, from_memberships


def trace(fig: go.Figure, meta: str):
    matches = [entry for entry in fig.data if entry.meta == meta]
    assert len(matches) == 1, f"expected exactly one {meta!r} trace"
    return matches[0]


def test_returns_figure_with_addressable_traces(sample):
    fig = create_upset(sample)
    assert isinstance(fig, go.Figure)
    metas = {entry.meta for entry in fig.data}
    assert metas == {
        "upset:intersection-bars",
        "upset:set-bars",
        "upset:matrix-background",
        "upset:matrix-connectors",
        "upset:matrix-dots",
    }


def test_intersection_bars_sorted_by_cardinality(sample):
    bars = trace(create_upset(sample), "upset:intersection-bars")
    # Empty intersection hidden by default; ties broken by degree then set order.
    assert [row[0] for row in bars.customdata] == ["A & B", "A", "B", "A & B & C"]
    assert list(bars.y) == [2, 1, 1, 1]


def test_set_bars_sorted_by_cardinality(sample):
    bars = trace(create_upset(sample), "upset:set-bars")
    assert [row[0] for row in bars.customdata] == ["A", "B", "C"]
    assert list(bars.x) == [4, 4, 1]


def test_matrix_dot_counts(sample):
    fig = create_upset(sample)
    background = trace(fig, "upset:matrix-background")
    dots = trace(fig, "upset:matrix-dots")
    assert len(background.x) == 4 * 3  # intersections x sets
    assert len(dots.x) == 2 + 1 + 1 + 3  # sum of shown degrees


def test_connectors_span_min_to_max_row(sample):
    connectors = trace(create_upset(sample), "upset:matrix-connectors")
    # Two multi-set intersections in display order: A & B at column 0 spanning
    # rows 0-1, and A & B & C at column 3 spanning rows 0-2.
    assert list(connectors.x) == [0, 0, None, 3, 3, None]
    assert list(connectors.y) == [0, 1, None, 0, 2, None]


def test_no_connector_trace_when_all_singletons():
    fig = create_upset(from_memberships([("A",), ("B",)]))
    assert all(entry.meta != "upset:matrix-connectors" for entry in fig.data)


def test_show_empty_includes_degree_zero(sample):
    bars = trace(create_upset(sample, show_empty=True), "upset:intersection-bars")
    labels = [row[0] for row in bars.customdata]
    assert "(no sets)" in labels
    assert len(labels) == 5


def test_sort_by_degree(sample):
    bars = trace(create_upset(sample, sort_by="degree"), "upset:intersection-bars")
    assert [row[1] for row in bars.customdata] == [1, 1, 2, 3]


def test_sort_sets_by_name():
    data = from_memberships([("b",), ("a", "b"), ("c",)])
    fig = create_upset(data, sort_sets_by="name")
    bars = trace(fig, "upset:set-bars")
    assert [row[0] for row in bars.customdata] == ["a", "b", "c"]


def test_show_counts_toggle(sample):
    labeled = trace(create_upset(sample), "upset:intersection-bars")
    bare = trace(create_upset(sample, show_counts=False), "upset:intersection-bars")
    assert labeled.texttemplate is not None
    assert bare.texttemplate is None


def test_show_percentages(sample):
    pct_only = trace(
        create_upset(sample, show_counts=False, show_percentages=True),
        "upset:intersection-bars",
    )
    assert pct_only.texttemplate == "%{customdata[2]}%"
    both = trace(
        create_upset(sample, show_counts=True, show_percentages=True),
        "upset:intersection-bars",
    )
    assert "%{y:,}" in both.texttemplate and "customdata[2]" in both.texttemplate
    neither = trace(
        create_upset(sample, show_counts=False, show_percentages=False),
        "upset:intersection-bars",
    )
    assert neither.texttemplate is None


def test_layout_passthrough(sample):
    fig = create_upset(sample, title="Movies", width=700, height=600)
    assert fig.layout.title.text == "Movies"
    assert fig.layout.width == 700
    assert fig.layout.height == 600


def test_default_height_scales_with_sets(sample):
    three_sets = create_upset(sample)
    one_set = create_upset(from_memberships([("A",)]))
    assert three_sets.layout.height > one_set.layout.height


def test_percentages_in_hover_data(sample):
    bars = trace(create_upset(sample), "upset:intersection-bars")
    # A & B holds 2 of 6 elements.
    assert bars.customdata[0][2] == "33.3"


def test_rejects_non_model_input():
    with pytest.raises((TypeError, ValueError)):
        create_upset(123)


def test_accepts_dataframe_with_sets():
    import pandas as pd

    df = pd.DataFrame({"A": [1, 1, 0], "B": [1, 0, 1], "note": ["x", "y", "z"]})
    fig = create_upset(df, sets=["A", "B"])
    names = {row[0] for row in trace(fig, "upset:set-bars").customdata}
    assert names == {"A", "B"}  # the "note" column is ignored


def test_accepts_polars_dataframe():
    import polars as pl

    df = pl.DataFrame({"A": [True, True, False], "B": [True, False, True]})
    fig = create_upset(df, sets=["A", "B"])
    assert {row[0] for row in trace(fig, "upset:set-bars").customdata} == {"A", "B"}


def test_rejects_empty_model():
    with pytest.raises(ValueError, match="no sets"):
        create_upset(from_memberships([]))


def test_rejects_all_empty_without_show_empty():
    data = UpSetData(("A",), (0,), (UpSetIntersection((), 5),))
    with pytest.raises(ValueError, match="show_empty"):
        create_upset(data)
    fig = create_upset(data, show_empty=True)
    assert len(trace(fig, "upset:intersection-bars").y) == 1


def test_filter_min_size(sample):
    bars = trace(create_upset(sample, min_subset_size=2), "upset:intersection-bars")
    assert [row[0] for row in bars.customdata] == ["A & B"]


def test_filter_max_degree(sample):
    bars = trace(create_upset(sample, max_degree=1), "upset:intersection-bars")
    assert all(row[1] <= 1 for row in bars.customdata)


def test_filter_top_n(sample):
    bars = trace(create_upset(sample, max_subsets=1), "upset:intersection-bars")
    assert len(bars.y) == 1


def test_over_filtering_errors(sample):
    with pytest.raises(ValueError, match="filter"):
        create_upset(sample, min_subset_size=1000)


def test_sort_by_deviation(sample):
    bars = trace(create_upset(sample, sort_by="deviation"), "upset:intersection-bars")
    labels = [row[0] for row in bars.customdata]
    assert labels[0] == "A & B & C"  # most surprising-large intersection first


def test_deviation_in_hover(sample):
    bars = trace(create_upset(sample), "upset:intersection-bars")
    # customdata carries a signed deviation string as its 4th field.
    assert all(len(row) == 4 for row in bars.customdata)
    assert bars.customdata[0][3].startswith(("+", "-"))


def test_mode_changes_bar_heights(sample):
    distinct = trace(create_upset(sample), "upset:intersection-bars")
    intersect = trace(create_upset(sample, mode="intersect"), "upset:intersection-bars")
    dmap = {row[0]: y for row, y in zip(distinct.customdata, distinct.y, strict=True)}
    imap = {row[0]: y for row, y in zip(intersect.customdata, intersect.y, strict=True)}
    assert dmap["A & B"] == 2  # exclusive: in exactly A and B
    assert imap["A & B"] == 3  # inclusive: in A and B (incl. A & B & C)


def test_mode_axis_title(sample):
    titles = [ax.title.text for ax in create_upset(sample, mode="union").select_yaxes()]
    assert "Union size" in titles


def test_invalid_mode_rejected(sample):
    with pytest.raises(ValueError, match="mode must be one of"):
        create_upset(sample, mode="nope")


def test_custom_colors(sample):
    fig = create_upset(sample, color="#123456", inactive_color="#abcdef")
    assert trace(fig, "upset:intersection-bars").marker.color == "#123456"
    assert trace(fig, "upset:matrix-background").marker.color == "#abcdef"


def test_theme_light_default(sample):
    assert create_upset(sample).layout.paper_bgcolor == "#ffffff"


def test_theme_dark_recolors(sample):
    dark = create_upset(sample, theme="dark")
    assert dark.layout.paper_bgcolor == "#1a1a19"
    assert trace(dark, "upset:intersection-bars").marker.color == "#e8e6e1"


def test_theme_auto_resolves_light(sample):
    assert create_upset(sample, theme="auto").layout.paper_bgcolor == "#ffffff"


def test_theme_palette_sets_colorway(sample):
    fig = create_upset(sample, theme="okabe-ito-dark")
    assert fig.layout.paper_bgcolor == "#1a1a19"
    assert list(fig.layout.colorway)[0] == "#E69F00"


def test_color_overrides_theme(sample):
    fig = create_upset(sample, theme="dark", color="#abc123", inactive_color="#def456")
    assert trace(fig, "upset:intersection-bars").marker.color == "#abc123"
    assert trace(fig, "upset:matrix-background").marker.color == "#def456"


def test_invalid_theme_rejected(sample):
    with pytest.raises(ValueError, match="theme must be one of"):
        create_upset(sample, theme="solarized")


def test_palette_colors_sets(sample):
    # A palette theme colors each set (its size bar + member dots) with the
    # colorway, so the CVD palettes visibly differ from plain light/dark.
    fig = create_upset(sample, theme="okabe-ito-light")
    set_bars = trace(fig, "upset:set-bars")
    assert set_bars.marker.color[0] == "#E69F00"  # per-set color array
    dots = trace(fig, "upset:matrix-dots")
    okabe = {"#E69F00", "#56B4E9", "#009E73", "#F0E442", "#0072B2", "#D55E00", "#CC79A7"}
    assert set(dots.marker.color) <= okabe


def test_plain_theme_sets_stay_ink(sample):
    set_bars = trace(create_upset(sample, theme="light"), "upset:set-bars")
    assert set(set_bars.marker.color) == {"#0b0b0b"}


def test_axis_titles_override(sample):
    fig = create_upset(sample, intersection_title="Errors", set_size_title="Total wrong")
    assert any(ax.title.text == "Errors" for ax in fig.select_yaxes())
    assert any(ax.title.text == "Total wrong" for ax in fig.select_xaxes())


def test_axis_titles_hidden(sample):
    fig = create_upset(sample, intersection_title=None, set_size_title=None)
    assert all(ax.title.text != "Set size" for ax in fig.select_xaxes())
    assert all(ax.title.text != "Intersection size" for ax in fig.select_yaxes())


def test_orientation_horizontal_default(sample):
    fig = create_upset(sample)
    assert trace(fig, "upset:intersection-bars").orientation in (None, "v")
    assert trace(fig, "upset:set-bars").orientation == "h"


def test_orientation_vertical_transposes(sample):
    fig = create_upset(sample, orientation="vertical")
    # Intersection bars become horizontal; set bars become vertical.
    assert trace(fig, "upset:intersection-bars").orientation == "h"
    assert trace(fig, "upset:set-bars").orientation in (None, "v")
    # Matrix dots' x now indexes sets (0..n_sets-1), not intersections.
    dots = trace(fig, "upset:matrix-dots")
    assert max(dots.x) <= len(sample.set_names) - 1


def test_invalid_orientation_rejected(sample):
    with pytest.raises(ValueError, match="orientation must be"):
        create_upset(sample, orientation="diagonal")


def test_description_auto_generated(sample):
    desc = create_upset(sample).layout.meta["description"]
    assert desc.startswith("UpSet plot of")
    assert "intersections" in desc


def test_description_override(sample):
    fig = create_upset(sample, description="Genes shared across three callers.")
    assert fig.layout.meta["description"] == "Genes shared across three callers."


def test_axis_ticks_hidden(sample):
    fig = create_upset(sample, show_set_size_ticks=False, show_intersection_ticks=False)
    set_axis = next(ax for ax in fig.select_xaxes() if ax.title.text == "Set size")
    intersection_axis = next(
        ax for ax in fig.select_yaxes() if ax.title.text == "Intersection size"
    )
    assert set_axis.showticklabels is False
    assert intersection_axis.showticklabels is False
