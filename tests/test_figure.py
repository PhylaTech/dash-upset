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
    with pytest.raises(TypeError, match="from_memberships"):
        create_upset({"A": 1})


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
