"""The interactive ``UpSet`` Dash component.

``UpSet`` is the Dash-native entry point: a component you drop into a layout
(like ``dcc.Graph`` or the sibling ``SeqViz``), not a figure. It builds the
UpSet figure from your data via :func:`~dash_upset.figure.create_upset` and
renders it with a compiled React component that turns clicks into two
declared, callback-addressable properties::

    from dash import Dash, html, Input, Output, callback
    from dash_upset import UpSet

    app = Dash(__name__)
    app.layout = html.Div([
        UpSet(id="genes", data=df, sets=["A", "B", "C"]),
        html.Pre(id="out"),
    ])

    @callback(Output("out", "children"), Input("genes", "selected_intersection"))
    def show(selection):
        return str(selection)

Selection properties (standard ``Input(id, property)`` addressing):

- ``selected_intersection`` -- ``{"label", "sets", "size"}`` when an
  intersection-size bar or a matrix dot is clicked (``size`` only for bars).
- ``selected_sets`` -- a list of set names when a set-size bar is clicked.

For notebooks, static export, or embedding a bare figure, use
:func:`~dash_upset.figure.create_upset` directly -- ``UpSet`` renders the same
figure and adds the interactive wiring on top.
"""

from __future__ import annotations

from dash_upset_component import DashUpset

from .figure import create_upset

__all__ = ["UpSet"]


class UpSet(DashUpset):
    """An interactive UpSet plot for a Dash layout.

    Args:
        data: A dataframe / mapping of boolean indicator columns, or an
            :class:`~dash_upset.data.UpSetData`. Same as
            :func:`~dash_upset.figure.create_upset`.
        sets: Columns to treat as sets when ``data`` is a dataframe.
        id: The component id, addressed from callbacks the standard Dash way:
            ``Input(id, "selected_intersection")`` /
            ``Input(id, "selected_sets")``.
        config: Optional plotly.js config override (defaults to a bare,
            responsive graph with no mode bar).
        style: CSS styles for the container div.
        className: CSS class for the container div.
        **kwargs: Forwarded to ``create_upset`` (``mode``, ``sort_by``,
            ``theme``, filtering, ...).
    """

    def __init__(
        self,
        data,
        sets=None,
        id=None,
        config=None,
        style=None,
        className=None,
        **kwargs,
    ):
        figure = create_upset(data, sets=sets, **kwargs)
        component_kwargs = {"figure": figure}
        # The generated component treats an explicit None as a value; only
        # pass what the caller set so its defaults stay in charge.
        if id is not None:
            component_kwargs["id"] = id
        if config is not None:
            component_kwargs["config"] = config
        if style is not None:
            component_kwargs["style"] = style
        if className is not None:
            component_kwargs["className"] = className
        super().__init__(**component_kwargs)
