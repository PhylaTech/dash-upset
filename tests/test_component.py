"""Tests for the UpSet Dash component.

``UpSet`` subclasses the compiled ``DashUpset`` React component
(``dash_upset_component``), building the figure from data and exposing click
selection as the declared ``selected_intersection`` / ``selected_sets``
properties. The click-to-selection mapping itself lives in JavaScript
(``src/lib/components/DashUpset.react.js``); here we cover the Python side:
construction, prop plumbing, and Dash registration.
"""

import pandas as pd
import plotly.graph_objects as go
import pytest

import dash_upset_component
from dash_upset import UpSet


def test_component_is_dash_component_with_figure():
    comp = UpSet(id="genes", data=pd.DataFrame({"A": [1, 0, 1], "B": [1, 1, 0]}))
    assert comp.id == "genes"
    assert isinstance(comp.figure, go.Figure)
    metas = {trace.meta for trace in comp.figure.data}
    assert "upset:intersection-bars" in metas


def test_component_registers_compiled_namespace():
    comp = UpSet(data=pd.DataFrame({"A": [1, 0], "B": [1, 1]}))
    assert comp._namespace == "dash_upset_component"
    assert comp._type == "DashUpset"


def test_selection_props_are_declared():
    comp = UpSet(data=pd.DataFrame({"A": [1, 0], "B": [1, 1]}))
    assert "selected_intersection" in comp._prop_names
    assert "selected_sets" in comp._prop_names


def test_component_forwards_create_upset_kwargs():
    comp = UpSet(id="g", data=pd.DataFrame({"A": [1, 0], "B": [1, 1]}), theme="dark")
    assert comp.figure.layout.paper_bgcolor == "#1a1a19"


def test_component_accepts_container_props():
    comp = UpSet(
        data=pd.DataFrame({"A": [1, 0], "B": [1, 1]}),
        config={"displayModeBar": True},
        style={"height": "300px"},
        className="my-upset",
    )
    assert comp.config == {"displayModeBar": True}
    assert comp.style == {"height": "300px"}
    assert comp.className == "my-upset"


def test_invalid_figure_kwargs_rejected():
    with pytest.raises(TypeError):
        UpSet(data=pd.DataFrame({"A": [1, 0]}), nonsense=True)


def test_highlight_props_declared_and_forwarded():
    comp = UpSet(
        data=pd.DataFrame({"A": [1, 0], "B": [1, 1]}),
        highlight_selection=False,
        selection_color="#ff0000",
    )
    assert "highlight_selection" in comp._prop_names
    assert "selection_color" in comp._prop_names
    assert comp.highlight_selection is False
    assert comp.selection_color == "#ff0000"


def test_axis_kwargs_reach_create_upset():
    comp = UpSet(
        data=pd.DataFrame({"A": [1, 0], "B": [1, 1]}),
        set_size_title=None,
        intersection_title="Errors",
    )
    assert any(ax.title.text == "Errors" for ax in comp.figure.select_yaxes())


def test_js_dist_points_at_committed_bundle():
    # Dash serves the compiled bundle from the inner package; the entries must
    # match files that actually ship (guards against a stale/renamed build).
    from pathlib import Path

    pkg_dir = Path(dash_upset_component.__file__).parent
    for dist in dash_upset_component._js_dist:
        assert (pkg_dir / dist["relative_package_path"]).is_file()
