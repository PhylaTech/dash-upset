"""Tests for the UpSet Dash All-in-One component.

The click callback is a thin wrapper over the pure ``_selection_from_click``
helper, which is unit-tested here without a Dash server. End-to-end callback
wiring is covered by the (selenium) integration layer.
"""

import pandas as pd
from dash import dcc, no_update

from dash_upset import UpSet
from dash_upset.component import _selection_from_click

# A minimal figure stub: only the stable trace order + meta ids matter.
FIG = {
    "data": [
        {"meta": "upset:intersection-bars"},
        {"meta": "upset:set-bars"},
        {"meta": "upset:matrix-background"},
        {"meta": "upset:matrix-dots"},
    ]
}


def test_component_builds_graph_and_stores():
    comp = UpSet(id="genes", data=pd.DataFrame({"A": [1, 0, 1], "B": [1, 1, 0]}))
    kinds = [type(child).__name__ for child in comp.children]
    assert kinds == ["Graph", "Store", "Store"]
    graph = comp.children[0]
    assert isinstance(graph, dcc.Graph)
    assert graph.id == UpSet.ids.graph("genes")
    assert graph.figure is not None


def test_ids_are_addressable():
    assert UpSet.ids.graph("x") == {"component": "UpSet", "subcomponent": "graph", "aio_id": "x"}
    assert UpSet.ids.selected_intersection("x")["subcomponent"] == "selected_intersection"
    assert UpSet.ids.selected_sets("x")["subcomponent"] == "selected_sets"


def test_component_forwards_create_upset_kwargs():
    comp = UpSet(id="g", data=pd.DataFrame({"A": [1, 0], "B": [1, 1]}), theme="dark")
    assert comp.children[0].figure.layout.paper_bgcolor == "#1a1a19"


def test_click_intersection_bar():
    click = {"points": [{"curveNumber": 0, "customdata": ["A & B", 2, "33.3", "+1.0"], "y": 5}]}
    intersection, sets = _selection_from_click(FIG, click)
    assert intersection == {"label": "A & B", "sets": ["A", "B"], "size": 5}
    assert sets is no_update


def test_click_set_bar():
    click = {"points": [{"curveNumber": 1, "customdata": ["A", "50.0"]}]}
    intersection, sets = _selection_from_click(FIG, click)
    assert sets == ["A"]
    assert intersection is no_update


def test_click_matrix_dot_selects_intersection():
    click = {"points": [{"curveNumber": 3, "customdata": ["A", "A & B (2)"]}]}
    intersection, sets = _selection_from_click(FIG, click)
    assert intersection == {"label": "A & B", "sets": ["A", "B"]}
    assert sets is no_update


def test_click_nothing_is_noop():
    intersection, sets = _selection_from_click(FIG, None)
    assert intersection is no_update
    assert sets is no_update
